import graphene
from graphene.relay import Node
from graphene_django import DjangoObjectType, DjangoConnectionField
from django.contrib.auth.hashers import make_password
from random import shuffle, randint

from db.types_revision import DocumentRevisionBase

from .models import (
    RANK_CHOICES, RANK_GENUS, RANK_SPECIES,
    LifeNode as LifeNodeModel,
    CommonName as CommonNameModel,
    Characteristic as CharacteristicModel
)
from commenting.models_graphql import CommentsNode
from voting.models_graphql import VotesNode
from images.models_graphql import Image
from tags.models_graphql import Tag


class Rank(graphene.Enum):
    KINGDOM = 10
    PHYLUM = 20
    CLASS = 30
    ORDER = 40
    FAMILY = 50
    GENUS = 60
    SPECIES = 70
    INFRASPECIES = 80
    VARIETY = 100

    @property
    def description(self):
        return dict(RANK_CHOICES)[self._value_]


class LifeNode(DocumentRevisionBase, CommentsNode, VotesNode,
               DjangoObjectType):
    parent = graphene.Field(lambda: LifeNode)
    parents = graphene.List(lambda: LifeNode)
    rank = graphene.Field(Rank)
    rankDisplay = graphene.String()

    commonNames = DjangoConnectionField(lambda: CommonName)
    children = DjangoConnectionField(lambda: LifeNode)
    images = DjangoConnectionField(Image)
    characteristics = DjangoConnectionField(lambda: Characteristic)

    class Meta:
        model = LifeNodeModel
        interfaces = (Node,)

    def resolve_parent(self, args, request, info):
        if self.parent:
            return self.parent.get_object()

    def resolve_parents(self, args, request, info):
        def get_parents(obj):
            parents = []
            if obj.parent:
                parent = obj.parent.get_object()
                parents.append(parent)
                parents.extend(get_parents(parent))
            return parents
        return get_parents(self)

    def resolve_rankDisplay(self, args, request, info):
        return self.get_rank_display()

    def resolve_commonNames(self, args, request, info):
        return CommonName._meta.model.objects.filter(
            document_id__in=self.commonNames.values_list('id', flat=True)
        ).order_by('name')

    def resolve_children(self, args, request, info):
        return LifeNode._meta.model.objects.filter(
            parent=self.document
        ).order_by('title')

    def resolve_images(self, args, context, info):
        return Image._meta.model.objects.filter(
            document_id__in=self.images.values_list('id', flat=True)
        )

    def resolve_characteristics(self, args, request, info):
        return Characteristic._meta.model.objects.filter(
            lifeNode=self.document
        )


class CommonName(DocumentRevisionBase, VotesNode, DjangoObjectType):
    class Meta:
        model = CommonNameModel
        interfaces = (Node,)


class Characteristic(DocumentRevisionBase, CommentsNode, VotesNode,
                     DjangoObjectType):
    tag = graphene.Field(lambda: Tag)
    title = graphene.String()

    class Meta:
        model = CharacteristicModel
        interfaces = (Node,)

    def resolve_tag(self, args, request, info):
        return self._get_tag()

    def resolve_title(self, args, request, info):
        return self._get_tag().title


class Quizz(graphene.ObjectType):
    image = graphene.Field(Image)
    choices = graphene.List(LifeNode)
    correct = graphene.String()

    class Meta:
        interfaces = (Node, )


def generate_quiz(root, args, context, info):
    image = Image._meta.model.objects.filter(
        document__lifeNode_image__rank__in=(RANK_GENUS, RANK_SPECIES)
    ).order_by('?').first()

    lifeNode = image.document.lifeNode_image.first()
    if lifeNode.rank == RANK_SPECIES:
        correct = lifeNode.parent.get_object()
    elif lifeNode.rank == RANK_GENUS:
        correct = lifeNode

    other_choices = LifeNode._meta.model.objects.filter(
        rank=RANK_GENUS
    ).exclude(document=correct.document).order_by('?')[:4]

    choices = [correct]
    for c in other_choices:
        choices.append(c)

    shuffle(choices)

    return Quizz(
        id=1,
        image=image,
        choices=choices,
        correct=make_password("%d" % correct.document_id, hasher='sha1')
    )
