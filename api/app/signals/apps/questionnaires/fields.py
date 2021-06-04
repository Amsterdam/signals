# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from collections import OrderedDict

from rest_framework import serializers

from signals.apps.questionnaires.mixins import HyperlinkedRelatedFieldMixin


class EmptyHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    def to_representation(self, value):
        return OrderedDict()


class QuestionnairePublicHyperlinkedIdentityField(HyperlinkedRelatedFieldMixin, serializers.HyperlinkedIdentityField):
    lookup_field = 'uuid'

    def to_representation(self, value):
        return OrderedDict([('self', dict(href=self.get_url(value, 'public-questionnaire-detail'))), ])


class QuestionnairePrivateHyperlinkedIdentityField(HyperlinkedRelatedFieldMixin, serializers.HyperlinkedIdentityField):
    def to_representation(self, value):
        return OrderedDict([
            ('self', dict(href=self.get_url(value, 'private-questionnaire-detail'))),
            ('sia:public-self', dict(href=self._reverse('public-questionnaire-detail', kwargs={'uuid': value.uuid}))),
        ])


class QuestionHyperlinkedIdentityField(HyperlinkedRelatedFieldMixin, serializers.HyperlinkedIdentityField):
    lookup_field = 'key'

    def to_representation(self, value):
        return OrderedDict([
            ('self', dict(href=self.get_url(value, 'public-question-detail'))),
            ('sia:uuid-self', dict(href=self._reverse('public-question-detail', kwargs={'key': value.uuid}))),
            ('sia:post-answer', dict(href=self._reverse('public-question-answer',
                                                        kwargs={'key': value.key or value.uuid}))),
        ])


class SessionPublicHyperlinkedIdentityField(HyperlinkedRelatedFieldMixin, serializers.HyperlinkedIdentityField):
    lookup_field = 'uuid'

    def to_representation(self, value):
        return OrderedDict([
            ('self', dict(href=self.get_url(value, 'public-session-detail'))),
            ('sia:questionnaire', dict(href=self._reverse('public-questionnaire-detail',
                                                          kwargs={'uuid': value.questionnaire.uuid})))
        ])
