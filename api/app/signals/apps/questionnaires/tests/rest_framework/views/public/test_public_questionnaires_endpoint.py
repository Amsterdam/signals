# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import include, path
from rest_framework.test import APITestCase

from signals.apps.api.views import NamespaceView
from signals.apps.questionnaires.factories import (
    ChoiceFactory,
    EdgeFactory,
    QuestionFactory,
    QuestionGraphFactory,
    QuestionnaireFactory
)
from signals.apps.questionnaires.models import (
    AttachedFile,
    AttachedSection,
    Questionnaire,
    StoredFile
)
from signals.apps.questionnaires.tests.mixin import ValidateJsonSchemaMixin

THIS_DIR = os.path.dirname(__file__)


urlpatterns = [
    path('v1/relations/', NamespaceView.as_view(), name='signal-namespace'),
    path('', include('signals.apps.questionnaires.urls')),
]


class NameSpace:
    pass


test_urlconf = NameSpace()
test_urlconf.urlpatterns = urlpatterns

THIS_DIR = os.path.dirname(__file__)
GIF_FILE = os.path.join(THIS_DIR, '..', '..', '..', 'test-data', 'test.gif')


@override_settings(ROOT_URLCONF=test_urlconf)
class TestPublicQuestionnaireEndpoint(ValidateJsonSchemaMixin, APITestCase):
    base_endpoint = '/public/qa/questionnaires/'

    def setUp(self):
        self.questionnaire = QuestionnaireFactory.create()

        self.detail_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../../json_schema/public_get_questionnaire_detail.json')
        )
        self.list_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../../json_schema/public_get_questionnaire_list.json')
        )

        # TODO: move this to factories
        self.attached_section_1 = AttachedSection.objects.create(
            title='TITLE 1',
            text='TEXT 1',
            content_object=self.questionnaire,
            order=2
        )
        self.attached_section_2 = AttachedSection.objects.create(
            title='TITLE 2',
            text='TEXT 2',
            content_object=self.questionnaire,
        )

        with open(GIF_FILE, 'rb') as f:
            suf = SimpleUploadedFile('test.gif', f.read(), content_type='image/gif')
            stored_file = StoredFile.objects.create(file=suf)

        self.attached_file_1 = AttachedFile.objects.create(
            stored_file=stored_file,
            description='IMAGE 1',
            section=self.attached_section_2
        )
        self.attached_file_2 = AttachedFile.objects.create(
            stored_file=stored_file,
            description='IMAGE 2',
            section=self.attached_section_2
        )

    def test_questionnaire_list(self):
        response = self.client.get(f'{self.base_endpoint}')
        self.assertEqual(response.status_code, 404)

        response_json = response.json()
        self.assertIn('attached_sections', response_json['results'][0])
        self.assertEqual(len(response_json['results'][0]['attached_sections']), 2)

    def test_questionnaire_detail_by_uuid(self):
        response = self.client.get(f'{self.base_endpoint}{self.questionnaire.uuid}')
        self.assertEqual(response.status_code, 200)
        response_json = response.json()

        self.assertJsonSchema(self.detail_schema, response_json)

        response_json = response.json()
        self.assertIn('attached_sections', response_json)
        self.assertEqual(len(response_json['attached_sections']), 2)
        self.assertEqual(response_json['attached_sections'][0]['order'], 0)
        self.assertEqual(response_json['attached_sections'][1]['order'], 2)

        self.assertEqual(len(response_json['attached_sections'][0]['attached_files']), 2)

    def test_questionnaire_create_not_allowed(self):
        response = self.client.post(f'{self.base_endpoint}', data={})
        self.assertEqual(response.status_code, 404)  # since there is no list endpoint, we cannot access it to create

    def test_questionnaire_update_not_allowed(self):
        response = self.client.patch(f'{self.base_endpoint}{self.questionnaire.uuid}', data={})
        self.assertEqual(response.status_code, 405)

    def test_questionnaire_delete_not_allowed(self):
        response = self.client.delete(f'{self.base_endpoint}{self.questionnaire.uuid}')
        self.assertEqual(response.status_code, 405)

    def test_create_session_for_questionnaire(self):
        q1 = QuestionFactory.create(analysis_key='q1', label='q1', short_label='q1')
        choice1_q2 = ChoiceFactory(question=q1, payload='q2', display='q2')
        choice1_q3 = ChoiceFactory(question=q1, payload='q3', display='q3')

        q2 = QuestionFactory.create(analysis_key='q2', label='q2', short_label='q2')
        q3 = QuestionFactory.create(analysis_key='q3', label='q3', short_label='q3')
        q4 = QuestionFactory.create(analysis_key='q4', label='q4', short_label='q4', required=True)
        q5 = QuestionFactory.create(analysis_key='q5', label='q5', short_label='q5')

        # sketch:
        #    q1 <- first_question
        #   /  \
        # q2    q3
        #   \  /
        #    q4
        #    |
        #    q5
        graph = QuestionGraphFactory.create(name='testgraph', first_question=q1)
        EdgeFactory.create(graph=graph, question=q1, next_question=q2, choice=choice1_q2)
        EdgeFactory.create(graph=graph, question=q2, next_question=q4, choice=None)
        EdgeFactory.create(graph=graph, question=q1, next_question=q3, choice=choice1_q3)
        EdgeFactory.create(graph=graph, question=q3, next_question=q4, choice=None)
        EdgeFactory.create(graph=graph, question=q4, next_question=q5, choice=None)

        questionnaire = QuestionnaireFactory.create(graph=graph, name='diamond', flow=Questionnaire.EXTRA_PROPERTIES)

        response = self.client.post(f'{self.base_endpoint}{questionnaire.uuid}/session', data=None, format='json')
        self.assertEqual(response.status_code, 201)

        response_json = response.json()
        self.assertIn('path_questions', response_json)
        self.assertEqual(len(response_json['path_questions']), 1)
        self.assertIn('path_answered_question_uuids', response_json)
        self.assertEqual(len(response_json['path_answered_question_uuids']), 0)
        self.assertIn('path_unanswered_question_uuids', response_json)
        self.assertEqual(len(response_json['path_unanswered_question_uuids']), 1)
        self.assertIn('path_validation_errors_by_uuid', response_json)
        self.assertEqual(len(response_json['path_validation_errors_by_uuid']), 0)
        self.assertIn('can_freeze', response_json)
        self.assertEqual(response_json['can_freeze'], False)
