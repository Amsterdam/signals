# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from collections import OrderedDict

from rest_framework import serializers


class QuestionnairePublicHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    lookup_field = 'uuid'

    def to_representation(self, value):
        request = self.context.get('request')
        _format = self.context.get('format', None)

        namespace = f'{request.resolver_match.namespace}:'

        result = OrderedDict([
            ('self', dict(href=self.get_url(value, f'{namespace}public-questionnaire-detail', request, _format))),
        ])

        return result


class QuestionnairePrivateHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    def to_representation(self, value):
        request = self.context.get('request')
        _format = self.context.get('format', None)

        namespace = f'{request.resolver_match.namespace}:'

        private_href = self.get_url(value, f'{namespace}private-questionnaire-detail', request, _format)
        public_href = self.reverse(f'{namespace}public-questionnaire-detail', kwargs={'uuid': value.uuid},
                                   request=request, format=_format)

        return OrderedDict([
            ('self', dict(href=private_href)),
            ('public', dict(href=public_href)),
        ])


class QuestionHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    lookup_field = 'key'

    def to_representation(self, value):
        request = self.context.get('request')
        _format = self.context.get('format', None)

        namespace = f'{request.resolver_match.namespace}:'

        self_href = self.get_url(value, f'{namespace}public-question-detail', request, _format)
        self_uuid_href = self.reverse(f'{namespace}public-question-detail', kwargs={'key': value.uuid}, request=request,
                                      format=_format)

        result = OrderedDict([
            ('self', dict(href=self_href)),
            ('self-uuid', dict(href=self_uuid_href)),
        ])

        return result


class SessionPublicHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    lookup_field = 'uuid'

    def to_representation(self, value):
        request = self.context.get('request')
        _format = self.context.get('format', None)

        namespace = f'{request.resolver_match.namespace}:'

        result = OrderedDict([
            ('self', dict(href=self.get_url(value, f'{namespace}public-session-detail', request, _format))),
        ])

        questionnaire = value.questionnaire
        if questionnaire:
            questionnaire_href = self.reverse(f'{namespace}public-questionnaire-detail',
                                              kwargs={'uuid': questionnaire.uuid}, request=request, format=_format)
            result.update({'sia:questionnaire': dict(href=questionnaire_href)})

        return result
