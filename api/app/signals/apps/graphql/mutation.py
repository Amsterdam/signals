import graphene
from graphene_django.rest_framework.mutation import SerializerMutation

from signals.apps.api.v1.serializers import PrivateQuestionSerializerDetail
from signals.apps.graphql.authorization import DeleteModelMutation, MutationPermissionSerializer
from signals.apps.graphql.types import QuestionType
from signals.apps.signals.models import Question


class DeleteQuestion(DeleteModelMutation, model=Question):
    pass


class QuestionMutationSerializer(PrivateQuestionSerializerDetail, MutationPermissionSerializer):
    pass


class QuestionMutation(SerializerMutation):

    class Meta:
        serializer_class = QuestionMutationSerializer
        convert_choices_to_enum = False
        model_operations = ('create', 'update',)
        lookup_field = 'id'

    question = graphene.Field(QuestionType)

    @classmethod
    def perform_mutate(cls, serializer, info):
        obj = serializer.save()
        return QuestionMutation(question=obj)
