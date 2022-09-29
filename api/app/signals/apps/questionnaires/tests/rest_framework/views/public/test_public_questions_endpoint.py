# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import include, path
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APITestCase

from signals.apps.api.views import NamespaceView
from signals.apps.questionnaires.factories import (
    AnswerFactory,
    EdgeFactory,
    QuestionFactory,
    QuestionGraphFactory,
    QuestionnaireFactory,
    SessionFactory
)
from signals.apps.questionnaires.models import (
    Answer,
    AttachedFile,
    AttachedSection,
    Session,
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
class TestPublicQuestionEndpoint(ValidateJsonSchemaMixin, APITestCase):
    base_endpoint = '/public/qa/questions/'

    def setUp(self):
        self.question = QuestionFactory.create()
        graph = QuestionGraphFactory.create(first_question=self.question)
        self.questionnaire = QuestionnaireFactory.create(graph=graph)

        self.detail_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../../json_schema/public_get_question_detail.json')
        )
        self.list_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../../json_schema/public_get_question_list.json')
        )
        self.post_answer_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../../json_schema/public_post_question_answer_response.json')
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

    def test_question_list(self):
        response = self.client.get(f'{self.base_endpoint}')
        self.assertEqual(response.status_code, 404)

    def test_question_detail(self):
        response = self.client.get(f'{self.base_endpoint}{self.question.uuid}')
        self.assertEqual(response.status_code, 200)

        self.assertJsonSchema(self.detail_schema, response.json())

    def test_question_create_not_allowed(self):
        response = self.client.post(f'{self.base_endpoint}', data={})
        self.assertEqual(response.status_code, 404)  # since there is no list endpoint, we cannot access it to create

    def test_question_update_not_allowed(self):
        response = self.client.patch(f'{self.base_endpoint}{self.question.uuid}', data={})
        self.assertEqual(response.status_code, 405)

    def test_question_delete_not_allowed(self):
        response = self.client.delete(f'{self.base_endpoint}{self.question.uuid}')
        self.assertEqual(response.status_code, 405)

    def test_answer_question_create(self):
        self.assertEqual(0, Answer.objects.count())
        self.assertEqual(0, Session.objects.count())

        data = {'payload': 'This is my answer for testing!', 'questionnaire': self.questionnaire.uuid}
        response = self.client.post(f'{self.base_endpoint}{self.question.uuid}/answer', data=data, format='json')
        self.assertEqual(response.status_code, 201)

        response_data = response.json()
        self.assertJsonSchema(self.post_answer_schema, response_data)

        self.assertEqual(1, Answer.objects.count())
        self.assertEqual(1, Session.objects.count())

        answer = Answer.objects.first()
        session = Session.objects.first()

        self.assertEqual(data['payload'], response_data['payload'])
        self.assertEqual(data['payload'], answer.payload)
        self.assertEqual(str(session.uuid), str(response_data['session']))
        self.assertIsNone(response_data['next_question'])

        self.assertEqual(answer.session.pk, session.pk)
        self.assertEqual(self.questionnaire.pk, session.questionnaire.pk)
        self.assertEqual(self.question.pk, answer.question.pk)

    def test_answer_question_create_existing_session(self):
        session = SessionFactory.create(questionnaire=self.questionnaire)

        self.assertEqual(0, Answer.objects.count())
        self.assertEqual(1, Session.objects.count())

        data = {'payload': 'This is my answer for testing!', 'session': session.uuid}
        response = self.client.post(f'{self.base_endpoint}{self.question.uuid}/answer', data=data, format='json')
        self.assertEqual(response.status_code, 201)

        response_data = response.json()
        self.assertJsonSchema(self.post_answer_schema, response_data)

        self.assertEqual(1, Answer.objects.count())
        self.assertEqual(1, Session.objects.count())

        answer = Answer.objects.first()
        session = Session.objects.first()

        self.assertEqual(data['payload'], response_data['payload'])
        self.assertEqual(data['payload'], answer.payload)
        self.assertEqual(str(session.uuid), str(response_data['session']))
        self.assertIsNone(response_data['next_question'])

    def test_answer_a_complete_questionnaire(self):
        self.assertEqual(0, Answer.objects.count())
        self.assertEqual(0, Session.objects.count())

        # Setup questions
        test_question_1 = QuestionFactory(retrieval_key='test-question-1')
        test_question_2 = QuestionFactory(retrieval_key='test-question-2')
        test_question_3 = QuestionFactory(retrieval_key='test-question-3')
        test_question_4 = QuestionFactory(retrieval_key='test-question-4')
        test_question_5 = QuestionFactory(retrieval_key='test-question-5')

        # Setup graph relations between questions
        graph = QuestionGraphFactory.create(first_question=test_question_1)
        EdgeFactory.create(graph=graph, question=test_question_1, next_question=test_question_2, choice=None)
        EdgeFactory.create(graph=graph, question=test_question_2, next_question=test_question_3, choice=None)
        EdgeFactory.create(graph=graph, question=test_question_3, next_question=test_question_4, choice=None)
        EdgeFactory.create(graph=graph, question=test_question_4, next_question=test_question_5, choice=None)

        # Create our questionnaire
        questionnaire = QuestionnaireFactory.create(graph=graph)

        # Answer our questionnaire
        data = {'payload': 'answer-1', 'questionnaire': questionnaire.uuid}
        first_post_answer_endpoint = f'{self.base_endpoint}{questionnaire.first_question.uuid}/answer'
        response = self.client.post(first_post_answer_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, 201)

        response_data = response.json()
        self.assertJsonSchema(self.post_answer_schema, response_data)
        self.assertIsNotNone(response_data['next_question'])

        self.assertEqual(1, Answer.objects.count())
        self.assertEqual(1, Session.objects.count())

        next_post_answer_endpoint = response_data['next_question']['_links']['sia:post-answer']['href']
        session = Session.objects.first()

        for x in range(2, 6):
            data = {'payload': f'answer-{x}', 'session': session.uuid}
            response = self.client.post(next_post_answer_endpoint, data=data, format='json')
            self.assertEqual(response.status_code, 201)

            response_data = response.json()
            self.assertJsonSchema(self.post_answer_schema, response_data)

            self.assertEqual(x, Answer.objects.count())
            self.assertEqual(1, Session.objects.count())

            if x < 5:
                self.assertIsNotNone(response_data['next_question'])
                next_post_answer_endpoint = response_data['next_question']['_links']['sia:post-answer']['href']
            else:
                self.assertIsNone(response_data['next_question'])  # session must be frozen using ../submit endpoint

        answer_qs = Answer.objects.filter(
            question_id__in=[
                questionnaire.graph.first_question.id,
                test_question_2.id,
                test_question_3.id,
                test_question_4.id,
                test_question_5.id,
            ],
            session_id=session.pk,
        )

        self.assertTrue(answer_qs.exists())
        self.assertEqual(5, answer_qs.count())

    def test_answer_a_complete_questionnaire_branching_flow(self):
        self.assertEqual(0, Answer.objects.count())
        self.assertEqual(0, Session.objects.count())

        # Setup questions
        test_question_1 = QuestionFactory(retrieval_key='test-question-1')
        test_question_2 = QuestionFactory(retrieval_key='test-question-2')
        test_question_3 = QuestionFactory(retrieval_key='test-question-3')
        test_question_4 = QuestionFactory(retrieval_key='test-question-4')

        # Setup graph relations between questions
        graph = QuestionGraphFactory.create(first_question=test_question_1)
        EdgeFactory.create(graph=graph,
                           question=test_question_1,
                           next_question=test_question_2,
                           choice__payload='yes',
                           choice__question=test_question_1)
        EdgeFactory.create(graph=graph,
                           question=test_question_1,
                           next_question=test_question_3,
                           choice__payload='no',
                           choice__question=test_question_1)
        EdgeFactory.create(graph=graph, question=test_question_1, next_question=test_question_4, choice=None)

        # Create our questionnaire
        questionnaire = QuestionnaireFactory.create(graph=graph)

        # Answer our questionnaire
        first_post_answer_endpoint = f'{self.base_endpoint}{questionnaire.first_question.uuid}/answer'

        # Flow: question 1 -> question 2 -> done
        data = {'payload': 'yes', 'questionnaire': questionnaire.uuid}
        response = self.client.post(first_post_answer_endpoint, data=data, format='json')
        response_data = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response_data['next_question']['uuid'], str(test_question_2.uuid))

        data = {'payload': 'test', 'session': response_data['session']}
        second_post_answer_endpoint = response_data['next_question']['_links']['sia:post-answer']['href']
        response = self.client.post(second_post_answer_endpoint, data=data, format='json')
        response_data = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response_data['next_question'])

        # Flow: question 1 -> question 3 -> done
        data = {'payload': 'no', 'questionnaire': questionnaire.uuid}
        response = self.client.post(first_post_answer_endpoint, data=data, format='json')
        response_data = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response_data['next_question']['uuid'], str(test_question_3.uuid))

        data = {'payload': 'test', 'session': response_data['session']}
        response = self.client.post(second_post_answer_endpoint, data=data, format='json')
        response_data = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response_data['next_question'])

        # Flow: question 1 -> question 4 -> done
        data = {'payload': 'default', 'questionnaire': questionnaire.uuid}
        response = self.client.post(first_post_answer_endpoint, data=data, format='json')
        response_data = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response_data['next_question']['uuid'], str(test_question_4.uuid))

        data = {'payload': 'test', 'session': response_data['session']}
        second_post_answer_endpoint = response_data['next_question']['_links']['sia:post-answer']['href']
        response = self.client.post(second_post_answer_endpoint, data=data, format='json')
        response_data = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response_data['next_question'])

        self.assertEqual(3, Session.objects.count())
        self.assertEqual(6, Answer.objects.count())

    def test_answer_question_create_invalid_data(self):
        self.assertEqual(0, Answer.objects.count())
        self.assertEqual(0, Session.objects.count())

        data = {'payload': {'value': 'This is my answer for testing!'}, }
        response = self.client.post(f'{self.base_endpoint}{self.question.uuid}/answer', data=data, format='json')
        self.assertEqual(response.status_code, 400)

        self.assertEqual(0, Answer.objects.count())
        self.assertEqual(0, Session.objects.count())

        data = {'payload': 'This is my answer for testing!',
                'session': '00000000-0000-0000-0000-000000000000',
                'questionnaire': '00000000-0000-0000-0000-000000000000'}
        response = self.client.post(f'{self.base_endpoint}{self.question.uuid}/answer', data=data, format='json')
        self.assertEqual(response.status_code, 400)

        self.assertEqual(0, Answer.objects.count())
        self.assertEqual(0, Session.objects.count())

        session = SessionFactory.create(questionnaire=self.questionnaire)
        data = {'payload': 'This is my answer for testing!',
                'session': session.uuid,
                'questionnaire': session.questionnaire.uuid}
        response = self.client.post(f'{self.base_endpoint}{self.question.uuid}/answer', data=data, format='json')
        self.assertEqual(response.status_code, 400)

        self.assertEqual(0, Answer.objects.count())
        self.assertEqual(1, Session.objects.count())

    def test_answer_question_create_frozen_session(self):
        session = SessionFactory.create(questionnaire=self.questionnaire, frozen=True)

        self.assertEqual(0, Answer.objects.count())
        self.assertEqual(1, Session.objects.count())

        data = {'payload': 'This is my answer for testing!', 'session': session.uuid}
        response = self.client.post(f'{self.base_endpoint}{self.question.uuid}/answer', data=data, format='json')
        self.assertEqual(response.status_code, 400)

        self.assertEqual(0, Answer.objects.count())
        self.assertEqual(1, Session.objects.count())

    def test_answer_question_create_session_submit_before_passed(self):
        now = timezone.now()
        with freeze_time(now - timezone.timedelta(hours=4)):
            session = SessionFactory.create(questionnaire=self.questionnaire,
                                            submit_before=now - timezone.timedelta(hours=2))

        self.assertEqual(0, Answer.objects.count())
        self.assertEqual(1, Session.objects.count())

        data = {'payload': 'This is my answer for testing!', 'session': session.uuid}
        response = self.client.post(f'{self.base_endpoint}{self.question.uuid}/answer', data=data, format='json')
        self.assertEqual(response.status_code, 400)

        self.assertEqual(0, Answer.objects.count())
        self.assertEqual(1, Session.objects.count())

    def test_answer_question_create_session_started_duration_passed(self):
        now = timezone.now()
        with freeze_time(now - timezone.timedelta(hours=4)):
            session = SessionFactory.create(questionnaire=self.questionnaire,
                                            started_at=now - timezone.timedelta(hours=3))

        self.assertEqual(0, Answer.objects.count())
        self.assertEqual(1, Session.objects.count())

        data = {'payload': 'This is my answer for testing!', 'session': session.uuid}
        response = self.client.post(f'{self.base_endpoint}{self.question.uuid}/answer', data=data, format='json')
        self.assertEqual(response.status_code, 400)

        self.assertEqual(0, Answer.objects.count())
        self.assertEqual(1, Session.objects.count())

    def test_answer_question_list_not_allowed(self):
        response = self.client.get(f'{self.base_endpoint}{self.question.uuid}/answer')
        self.assertEqual(response.status_code, 405)

    def test_answer_question_detail_not_allowed(self):
        answer = AnswerFactory.create()

        response = self.client.get(f'{self.base_endpoint}{self.question.uuid}/answer/{answer.pk}')
        self.assertEqual(response.status_code, 404)

    def test_answer_question_update_not_allowed(self):
        response = self.client.patch(f'{self.base_endpoint}{self.question.uuid}/answer', data={})
        self.assertEqual(response.status_code, 405)

    def test_answer_question_delete_not_allowed(self):
        response = self.client.delete(f'{self.base_endpoint}{self.question.uuid}/answer')
        self.assertEqual(response.status_code, 405)
