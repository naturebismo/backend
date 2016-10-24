import graphene
from graphql_relay.node.node import from_global_id
from graphql_relay.connection.arrayconnection import offset_to_cursor

from accounts.decorators import login_required
from backend.mutations import Mutation
from db.models_graphql import Document
from .models_graphql import WhatIsThis, SuggestionID


class WhatIsThisCreate(Mutation):
    class Input:
        when = graphene.String(required=False)
        where = graphene.String(required=False)
        notes = graphene.String(required=False)

    whatisthis = graphene.Field(WhatIsThis.Connection.Edge)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, input, request, info):
        what = WhatIsThis._meta.model()
        what.author = request.user.document
        what.when = input.get('when')
        what.where = input.get('where')
        what.notes = input.get('notes')
        what.save(request=request)
        return WhatIsThisCreate(
            whatisthis=WhatIsThis.Connection.Edge(node=what,
                                                  cursor=offset_to_cursor(0)),
        )


class SuggestionIDCreate(Mutation):
    class Input:
        whatisthis = graphene.ID(required=True)
        identification = graphene.ID(required=True)
        notes = graphene.String(required=False)

    suggestionid = graphene.Field(SuggestionID.Connection.Edge)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, input, request, info):
        suggestion = SuggestionID._meta.model()
        suggestion.author = request.user.document

        gid_type, gid = from_global_id(input.get('whatisthis'))
        suggestion.whatisthis = Document._meta.model.objects.get(pk=gid)

        gid_type, gid = from_global_id(input.get('identification'))
        suggestion.identification = Document._meta.model.objects.get(pk=gid)

        suggestion.notes = input.get('notes')
        suggestion.save(request=request)

        return SuggestionIDCreate(
            suggestionid=SuggestionID.Connection.Edge(
                node=suggestion, cursor=offset_to_cursor(0)
            ),
        )