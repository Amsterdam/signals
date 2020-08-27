import graphene
from graphene_django.filter import DjangoFilterConnectionField

from signals.apps.graphql.types import CategoryType, DepartmentType, QuestionType
from signals.apps.signals.models import Question


class CategoryQuery:
    category = graphene.relay.Node.Field(CategoryType)
    categories = DjangoFilterConnectionField(CategoryType)


class DepartmentQuery:
    department = graphene.relay.Node.Field(DepartmentType)
    departments = DjangoFilterConnectionField(DepartmentType)


class QuestionQuery:
    question = graphene.Field(QuestionType, id=graphene.Int())
    questions = DjangoFilterConnectionField(QuestionType)

    def resolve_question(self, info, id):
        return Question.objects.get(pk=id)
