# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from collections import OrderedDict

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.relations import RelatedField

from signals.apps.questionnaires.rest_framework.mixins import HyperlinkedRelatedFieldMixin


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


class EmptyHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    def to_representation(self, value):
        return OrderedDict()


class QuestionnairePublicHyperlinkedIdentityField(HyperlinkedRelatedFieldMixin, serializers.HyperlinkedIdentityField):
    lookup_field = 'uuid'

    def to_representation(self, value):
        return OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=self.context.get('request')))),
            ('self', dict(href=self._get_url(value, 'public-questionnaire-detail'))),
            ('sia:create-session', dict(href=self._get_url(value, 'public-questionnaire-create-session'))),
        ])


class QuestionHyperlinkedIdentityField(HyperlinkedRelatedFieldMixin, serializers.HyperlinkedIdentityField):
    lookup_field = 'retrieval_key'

    def to_representation(self, value):
        return OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=self.context.get('request')))),
            ('self', dict(href=self._get_url(value, 'public-question-detail'))),
            ('sia:uuid-self', dict(href=self._reverse('public-question-detail', kwargs={'retrieval_key': value.uuid}))),
            ('sia:post-answer', dict(href=self._reverse('public-question-answer',
                                                        kwargs={'retrieval_key': value.retrieval_key or value.uuid}))),
        ])


class SessionPublicHyperlinkedIdentityField(HyperlinkedRelatedFieldMixin, serializers.HyperlinkedIdentityField):
    lookup_field = 'uuid'

    def to_representation(self, value):
        result = OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=self.context.get('request')))),
            ('self', dict(href=self._get_url(value, 'public-session-detail'))),
            ('sia:questionnaire', dict(href=self._reverse('public-questionnaire-detail',
                                                          kwargs={'uuid': value.questionnaire.uuid})))
        ])

        if value._signal:
            result.update({
                'sia:public-signal': dict(
                    href=self.get_url(value._signal, 'public-signals-detail', self.context.get('request'), None)
                )
            })

        return result
