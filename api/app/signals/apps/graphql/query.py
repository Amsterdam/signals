import graphene
from graphene_django.filter import DjangoFilterConnectionField

from signals.apps.graphql.types import CategoryType, DepartmentType


class CategoryQuery:
    category = graphene.relay.Node.Field(CategoryType)
    categories = DjangoFilterConnectionField(CategoryType)


class DepartmentQuery:
    department = graphene.relay.Node.Field(DepartmentType)
    departments = DjangoFilterConnectionField(DepartmentType)
