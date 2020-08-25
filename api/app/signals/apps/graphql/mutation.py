import graphene
from graphql_relay.node.node import from_global_id
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.forms.mutation import DjangoFormMutation
from graphene_django.rest_framework.mutation import SerializerMutation
from signals.apps.api.v1.serializers import PrivateQuestionSerializerDetail
from signals.apps.signals.models import Question
from signals.apps.graphql.types import QuestionType

'''
class QuestionInput(graphene.InputObjectType):
    key = graphene.String(required=True)
    field_type = graphene.String(required=True)
    meta = graphene.JSONString(required=True)
    required = graphene.Boolean(required=False)
'''

class QuestionMutation(SerializerMutation):
    class Meta:
        serializer_class = PrivateQuestionSerializerDetail
        convert_choices_to_enum = False
        model_operations = ('create', 'update',)
        lookup_field = 'id'

    question = graphene.Field(QuestionType)

    @classmethod
    def perform_mutate(cls, serializer, info):
        obj = serializer.save()
        return QuestionMutation(question=obj)
