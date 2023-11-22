# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from collections import OrderedDict
from typing import Mapping, Any

from datapunt_api.serializers import LinksField
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from rest_framework.relations import RelatedField
from rest_framework.reverse import reverse

from signals.apps.questionnaires.models import Questionnaire, Session, Answer, Question


class UUIDRelatedField(RelatedField):
    default_error_messages = {
        'does_not_exist': 'Object does not exist.',
        'invalid': 'Invalid value given.',
    }

    def __init__(self, uuid_field=None, **kwargs):
        self.uuid_field = uuid_field or 'uuid'
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(**{self.uuid_field: data})
        except ObjectDoesNotExist:
            self.fail('does_not_exist', slug_name=self.uuid_field, value=data)
        except (TypeError, ValueError):
            self.fail('invalid')

    def to_representation(self, obj):
        return getattr(obj, self.uuid_field)


class EmptyHyperlinkedIdentityField(LinksField):
    def to_representation(self, value: Answer) -> OrderedDict:
        return OrderedDict()


class BaseQuestionnaireLinksField(LinksField):
    def _get_url(self, obj: Model, view_name: str) -> str | None:
        request = self.context.get('request')
        namespace = request.resolver_match.namespace if request else None
        if namespace:
            view_name = f'{namespace}:{view_name}'
        return super().get_url(obj=obj, view_name=view_name, request=request, format=self.context.get('format'))

    def _reverse(self, view_name: str, kwargs: Mapping[str, Any]) -> str:
        request = self.context.get('request')
        namespace = request.resolver_match.namespace if request else None
        if namespace:
            view_name = f'{namespace}:{view_name}'
        return reverse(view_name, kwargs=kwargs, request=request, format=self.context.get('format'))


class QuestionnairePublicLinksField(BaseQuestionnaireLinksField):
    lookup_field = 'uuid'

    def to_representation(self, value: Questionnaire) -> OrderedDict:
        return OrderedDict([
            ('curies', {
                'name': 'sia',
                'href': reverse('signal-namespace', request=self.context.get('request'))
            }),
            ('self', {'href': self._get_url(value, 'public-questionnaire-detail')}),
            ('sia:create-session', {'href': self._get_url(value, 'public-questionnaire-create-session')}),
        ])


class QuestionHyperlinkedIdentityField(BaseQuestionnaireLinksField):
    lookup_field = 'retrieval_key'

    def to_representation(self, value: Question) -> OrderedDict:
        return OrderedDict([
            ('curies', {
                'name': 'sia',
                'href': reverse('signal-namespace', request=self.context.get('request'))
            }),
            ('self', {'href': self._get_url(value, 'public-question-detail')}),
            ('sia:uuid-self', {'href': self._reverse('public-question-detail', kwargs={'retrieval_key': value.uuid})}),
            ('sia:post-answer', {
                'href': self._reverse(
                    'public-question-answer',
                    kwargs={'retrieval_key': value.retrieval_key or value.uuid}
                )
            }),
        ])


class SessionPublicLinksField(BaseQuestionnaireLinksField):
    lookup_field = 'uuid'

    def to_representation(self, value: Session) -> OrderedDict:
        result = OrderedDict([
            ('curies', {
                'name': 'sia',
                'href': reverse('signal-namespace', request=self.context.get('request'))
            }),
            ('self', {'href': self._get_url(value, 'public-session-detail')}),
            ('sia:questionnaire', {
                'href': self._reverse('public-questionnaire-detail', kwargs={'uuid': value.questionnaire.uuid})
            }),
            ('sia:post-answers', {'href': self._reverse('public-session-answers', kwargs={'uuid': value.uuid})}),
            ('sia:post-attachments', {
                'href': self._reverse('public-session-attachments', kwargs={'uuid': value.uuid})
            }),
            ('sia:post-submit', {'href': self._reverse('public-session-submit', kwargs={'uuid': value.uuid})}),
        ])

        if value._signal:
            result.update({
                'sia:public-signal': {
                    'href': self.get_url(value._signal, 'public-signals-detail', self.context.get('request'), None)
                }
            })

        return result
