import graphene
from graphql_relay.node.node import from_global_id

from accounts.decorators import login_required
from accounts.permissions import has_permission
from db.models_graphql import Document
from backend.mutations import Mutation
from .models_graphql import Comment, Commenting


def comment_save(comment, args, request):
    comment.body = args.get('body')
    comment.save(request=request)
    return comment


class CommentEdge(graphene.ObjectType):
    node = graphene.Field(Comment)
    cursor = graphene.String(required=True)


class CommentCreate(Mutation):
    class Input:
        parent = graphene.ID(required=True)
        body = graphene.String(required=True)

    comment = graphene.Field(CommentEdge)
    commenting = graphene.Field(Commenting)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, input, request, info):
        comment = Comment._meta.model()

        gid_type, gid = from_global_id(input.get('parent'))
        comment.parent = Document._meta.model.objects.get(pk=gid)

        comment = comment_save(comment, input, request)

        # schema = info.schema.graphene_schema
        # object_type = schema.get_type(gid_type)
        # parent = object_type(object_type.get_node(gid, request, info))

        return CommentCreate(
            comment=CommentEdge(node=comment, cursor='.'),
            commenting=Commenting.get_node(gid, request, info)
        )


class CommentEdit(Mutation):
    class Input:
        id = graphene.ID(required=True)
        body = graphene.String(required=True)

    comment = graphene.Field(Comment)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, input, request, info):
        gid_type, gid = from_global_id(input.get('id'))
        comment = Comment._meta.model.objects.get(document_id=gid)

        error = has_permission(cls, request, comment, 'edit')
        if error:
            return error

        comment = comment_save(comment, input, request)
        return CommentEdit(comment=comment)


class CommentDelete(Mutation):
    class Input:
        id = graphene.ID(required=True)

    commentDeletedID = graphene.ID(required=True)
    commenting = graphene.Field(Commenting)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, input, request, info):
        gid_type, gid = from_global_id(input.get('id'))
        comment = Comment._meta.model.objects.get(document_id=gid)

        error = has_permission(cls, request, comment, 'delete')
        if error:
            return error

        parent_id = comment.parent_id
        comment.delete(request=request)

        return CommentDelete(
            commentDeletedID=input.get('id'),
            commenting=Commenting.get_node(parent_id, request, info)
        )
