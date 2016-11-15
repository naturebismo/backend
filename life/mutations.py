import graphene
from graphql_relay.node.node import from_global_id

from accounts.decorators import login_required
from accounts.permissions import has_permission
from db.models_graphql import Document
from backend.mutations import Mutation
from .models_graphql import LifeNode
from .models import (
    RANK_BY_STRING, CommonName,
    LifeNode as LifeNodeModel
)


def node_save(node, args, request):
    node.title = args.get('title')
    node.description = args.get('description')
    node.gbif_id = args.get('gbif_id')
    node.rank = RANK_BY_STRING[args.get('rank')]

    parent_id = args.get('parent')
    if parent_id:
        gid_type, gid = from_global_id(parent_id)
        node.parent = Document._meta.model.objects.get(pk=gid)

    node.save(request=request)

    commonNames = args.get('commonNames', [])
    for commonNameDict in commonNames:
        commonName_str = commonNameDict['name'].strip(' \t\n\r')

        if len(commonName_str) == 0:
            # don't save empty
            continue

        try:
            commonName = CommonName.objects.get(name=commonName_str)
        except CommonName.DoesNotExist:
            commonName = CommonName(
                name=commonName_str,
                language=commonNameDict['language']
            )
            commonName.save(request=request)
        node.commonNames.add(commonName.document)

    return node


class CommonNameInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    language = graphene.String(required=False)


class LifeNodeCreate(Mutation):
    class Input:
        title = graphene.String(required=True)
        description = graphene.String()
        rank = graphene.String(required=True)
        parent = graphene.ID()
        gbif_id = graphene.Int()
        commonNames = graphene.List(CommonNameInput)

    lifeNode = graphene.Field(LifeNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, input, request, info):
        node = LifeNode._meta.model()
        node = node_save(node, input, request)
        return LifeNodeCreate(lifeNode=node)


class LifeNodeEdit(Mutation):
    class Input:
        id = graphene.ID(required=True)
        title = graphene.String(required=True)
        description = graphene.String()
        rank = graphene.String(required=True)
        parent = graphene.ID()
        gbif_id = graphene.Int()
        commonNames = graphene.List(CommonNameInput)

    lifeNode = graphene.Field(LifeNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, input, request, info):
        gid_type, gid = from_global_id(input.get('id'))
        node = LifeNode._meta.model.objects.get(document_id=gid)

        error = has_permission(cls, request, node, 'edit')
        if error:
            return error

        node = node_save(node, input, request)
        return LifeNodeEdit(lifeNode=node)


class LifeNodeDelete(Mutation):
    class Input:
        id = graphene.ID(required=True)

    lifeNodeDeletedID = graphene.ID(required=True)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, input, request, info):
        gid_type, gid = from_global_id(input.get('id'))
        node = LifeNode._meta.model.objects.get(document_id=gid)

        error = has_permission(cls, request, node, 'delete')
        if error:
            return error

        node.delete(request=request)

        return LifeNodeDelete(lifeNodeDeletedID=input.get('id'))


class SpeciesCreate(Mutation):
    class Input:
        commonNames = graphene.String(required=False)
        species = graphene.String(required=True)
        genus = graphene.String(required=True)
        family = graphene.String(required=False)

    species = graphene.Field(LifeNode)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, input, request, info):
        genus_qs = LifeNodeModel.objects.filter(
            title__iexact=input.get('genus'),
            rank=RANK_BY_STRING['genus'])

        genus = None
        family = None

        if genus_qs.count() > 0:
            genus = genus_qs[0]
        elif len(input.get('genus')) > 0:
            family_qs = LifeNodeModel.objects.filter(
                title__iexact=input.get('family'),
                rank=RANK_BY_STRING['family'])
            if family_qs.count() > 0:
                family = family_qs[0]
            elif len(input.get('family')) > 0:
                family = LifeNodeModel(
                    rank=RANK_BY_STRING['family'],
                    title=input.get('family')
                )
                family.save(request=request)
            genus = LifeNodeModel(
                rank=RANK_BY_STRING['genus'],
                title=input.get('genus'),
                parent=family.document if family else None
            )
            genus.save(request=request)

        species = LifeNodeModel(
            parent=genus.document if genus else None,
            rank=RANK_BY_STRING['species'],
            title=input.get('species'),
        )
        species.save(request=request)

        commonNames_raw = input.get('commonNames', '')
        for commonName_str in commonNames_raw.split(','):
            commonName_str = commonName_str.strip(' \t\n\r')

            if len(commonName_str) == 0:
                # don't save empty
                continue

            try:
                commonName = CommonName.objects.get(name=commonName_str)
            except CommonName.DoesNotExist:
                commonName = CommonName(
                    name=commonName_str,
                )
                commonName.save(request=request)
            species.commonNames.add(commonName.document)

        return SpeciesCreate(species=species)
