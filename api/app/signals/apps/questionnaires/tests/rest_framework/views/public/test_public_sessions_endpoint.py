# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import os
import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import include, path
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APITestCase

from signals.apps.api.generics.routers import SignalsRouter
from signals.apps.api.views import NamespaceView, PublicSignalViewSet
from signals.apps.questionnaires.factories import (
    ChoiceFactory,
    EdgeFactory,
    QuestionFactory,
    QuestionGraphFactory,
    QuestionnaireFactory,
    SessionFactory
)
from signals.apps.questionnaires.models import Question, Questionnaire
from signals.apps.questionnaires.tests.mixin import ValidateJsonSchemaMixin
from signals.apps.signals.factories import SignalFactory, StatusFactory
from signals.apps.signals.tests.attachment_helpers import small_gif
from signals.apps.signals.workflow import GEMELD, REACTIE_GEVRAAGD

THIS_DIR = os.path.dirname(__file__)


extra_router = SignalsRouter()
extra_router.register(r'public/signals', PublicSignalViewSet, basename='public-signals')


urlpatterns = [
    path('v1/relations/', NamespaceView.as_view(), name='signal-namespace'),
    path('', include('signals.apps.questionnaires.urls')),
]


class NameSpace:
    pass


test_urlconf = NameSpace()
test_urlconf.urlpatterns = urlpatterns + extra_router.urls


@override_settings(ROOT_URLCONF=test_urlconf)
class TestPublicSessionEndpoint(ValidateJsonSchemaMixin, APITestCase):
    base_endpoint = '/public/qa/sessions/'

    def setUp(self):
        self.questionnaire = QuestionnaireFactory.create()
        self.session = SessionFactory.create(questionnaire=self.questionnaire)

        self.detail_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../../json_schema/public_get_session_detail.json')
        )

    def test_session_detail(self):
        response = self.client.get(f'{self.base_endpoint}{self.session.uuid}')
        self.assertEqual(response.status_code, 200)
        self.assertJsonSchema(self.detail_schema, response.json())

    def test_session_detail_gone(self):
        now = timezone.now()
        with freeze_time(now - timezone.timedelta(days=1)):
            session = SessionFactory.create(questionnaire=self.questionnaire,
                                            started_at=now - timezone.timedelta(hours=6))

        response = self.client.get(f'{self.base_endpoint}{session.uuid}')
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json()['detail'], 'Expired!')

        now = timezone.now()
        with freeze_time(now - timezone.timedelta(days=1)):
            session = SessionFactory.create(questionnaire=self.questionnaire,
                                            submit_before=now-timezone.timedelta(hours=1))

        response = self.client.get(f'{self.base_endpoint}{session.uuid}')
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json()['detail'], 'Expired!')

    def test_session_detail_frozen(self):
        session = SessionFactory.create(questionnaire=self.questionnaire, frozen=True)

        response = self.client.get(f'{self.base_endpoint}{session.uuid}')
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json()['detail'], 'Already used!')

    def test_session_detail_reaction_requested(self):
        questionnaire = QuestionnaireFactory.create(flow=Questionnaire.REACTION_REQUEST)

        session = SessionFactory.create(questionnaire=questionnaire)

        response = self.client.get(f'{self.base_endpoint}{session.uuid}')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['detail'], f'Session {session.uuid} is not associated with a Signal.')

        signal = SignalFactory.create(status__state=GEMELD)
        session._signal = signal
        session.save()

        response = self.client.get(f'{self.base_endpoint}{session.uuid}')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['detail'],
                         f'Session {session.uuid} is invalidated, associated signal not in state REACTIE_GEVRAAGD.')

        status = StatusFactory(state=REACTIE_GEVRAAGD, _signal=signal)
        signal.status = status
        signal.save()

        latest_session = SessionFactory.create(questionnaire=questionnaire, _signal=signal)

        response = self.client.get(f'{self.base_endpoint}{session.uuid}')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['detail'],
                         f'Session {session.uuid} is invalidated, a newer reaction request was issued.')

        response = self.client.get(f'{self.base_endpoint}{latest_session.uuid}')
        self.assertEqual(response.status_code, 200)

    def test_session_list_not_found(self):
        response = self.client.get(f'{self.base_endpoint}')
        self.assertEqual(response.status_code, 404)

    def test_session_create_not_found(self):
        response = self.client.post(f'{self.base_endpoint}', data={})
        self.assertEqual(response.status_code, 404)

    def test_session_update_not_allowed(self):
        response = self.client.patch(f'{self.base_endpoint}{self.questionnaire.uuid}', data={})
        self.assertEqual(response.status_code, 405)

    def test_session_delete_not_allowed(self):
        response = self.client.delete(f'{self.base_endpoint}{self.questionnaire.uuid}')
        self.assertEqual(response.status_code, 405)

    def test_session_submit(self):
        session = SessionFactory.create(questionnaire=self.questionnaire)

        response = self.client.post(f'{self.base_endpoint}{session.uuid}/submit/')
        self.assertEqual(response.status_code, 200)
        session.refresh_from_db()

        response = self.client.post(f'{self.base_endpoint}{session.uuid}/submit/')
        self.assertEqual(response.status_code, 410)

        generated = uuid.uuid4()
        while generated == session.uuid:
            generated = uuid.uuid4()
        response = self.client.post(f'{self.base_endpoint}{str(generated)}/submit/')

        self.assertEqual(response.status_code, 404)


@override_settings(ROOT_URLCONF=test_urlconf)
class TestPublicSessionEndpointAnswerFlow(ValidateJsonSchemaMixin, APITestCase):
    base_endpoint = '/public/qa/sessions/'

    def _get_questionnaire(self):
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

        return QuestionnaireFactory.create(graph=graph, name='diamond', flow=Questionnaire.EXTRA_PROPERTIES)

    def setUp(self):
        self.questionnaire = self._get_questionnaire()
        self.session = SessionFactory(questionnaire=self.questionnaire, submit_before=None, duration=None, frozen=False)

    def test_create_session(self):
        pass

    def test_retrieve_session(self):
        response = self.client.get(f'{self.base_endpoint}{self.session.uuid}')
        self.assertEqual(response.status_code, 200)
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

    def test_answer_question_incorrectly(self):
        question = Question.objects.get(analysis_key='q1')
        answer_data = [{
            'question_uuid': str(question.uuid),
            'payload': False
        }]
        request = self.client.post(f'{self.base_endpoint}{self.session.uuid}/answers', data=answer_data, format='json')
        self.assertEqual(request.status_code, 200)  # Think about status code! (maybe 202)
        response_json = request.json()

        self.assertIn('path_questions', response_json)
        self.assertEqual(len(response_json['path_questions']), 1)
        self.assertIn('path_answered_question_uuids', response_json)
        self.assertEqual(len(response_json['path_answered_question_uuids']), 0)
        self.assertIn('path_unanswered_question_uuids', response_json)
        self.assertEqual(len(response_json['path_unanswered_question_uuids']), 1)
        self.assertIn('path_validation_errors_by_uuid', response_json)
        self.assertEqual(len(response_json['path_validation_errors_by_uuid']), 1)
        self.assertIn(str(question.uuid), response_json['path_validation_errors_by_uuid'])  # TBD, details of errors
        self.assertIn('can_freeze', response_json)
        self.assertEqual(response_json['can_freeze'], False)

    def test_answer_question_correctly(self):
        question = Question.objects.get(analysis_key='q1')
        answer_data = [{
            'question_uuid': str(question.uuid),
            'payload': 'q2'
        }]
        request = self.client.post(f'{self.base_endpoint}{self.session.uuid}/answers', data=answer_data, format='json')
        self.assertEqual(request.status_code, 200)  # Think about status code! (maybe 202)
        response_json = request.json()

        self.assertIn('path_questions', response_json)
        self.assertEqual(len(response_json['path_questions']), 4)
        self.assertIn('path_answered_question_uuids', response_json)
        self.assertEqual(len(response_json['path_answered_question_uuids']), 1)
        self.assertIn(str(question.uuid), response_json['path_answered_question_uuids'])
        self.assertIn('path_unanswered_question_uuids', response_json)
        self.assertEqual(len(response_json['path_unanswered_question_uuids']), 3)
        self.assertIn('path_validation_errors_by_uuid', response_json)
        self.assertEqual(len(response_json['path_validation_errors_by_uuid']), 0)
        self.assertIn('can_freeze', response_json)
        self.assertEqual(response_json['can_freeze'], False)

    def test_answer_all_questions(self):
        q1 = Question.objects.get(analysis_key='q1')
        q2 = Question.objects.get(analysis_key='q2')
        q3 = Question.objects.get(analysis_key='q4')
        q4 = Question.objects.get(analysis_key='q5')
        answer_data = [
            {'question_uuid': str(q1.uuid), 'payload': 'q2'},
            {'question_uuid': str(q2.uuid), 'payload': 'AAA'},
            {'question_uuid': str(q3.uuid), 'payload': 'AAA'},
            {'question_uuid': str(q4.uuid), 'payload': 'AAA'},
        ]

        request = self.client.post(f'{self.base_endpoint}{self.session.uuid}/answers', data=answer_data, format='json')
        self.assertEqual(request.status_code, 200)  # Think about status code! (maybe 202)
        response_json = request.json()

        self.assertIn('path_questions', response_json)
        self.assertEqual(len(response_json['path_questions']), 4)
        self.assertIn('path_answered_question_uuids', response_json)

        # TODO: debug problem where one answer does not show up.
        self.assertIn(str(q1.uuid), response_json['path_answered_question_uuids'])
        self.assertIn(str(q2.uuid), response_json['path_answered_question_uuids'])
        self.assertIn(str(q3.uuid), response_json['path_answered_question_uuids'])
        self.assertIn(str(q4.uuid), response_json['path_answered_question_uuids'])
        self.assertEqual(len(response_json['path_answered_question_uuids']), 4)

        self.assertIn('path_unanswered_question_uuids', response_json)
        self.assertEqual(len(response_json['path_unanswered_question_uuids']), 0)
        self.assertIn('path_validation_errors_by_uuid', response_json)
        self.assertEqual(len(response_json['path_validation_errors_by_uuid']), 0)
        self.assertIn('can_freeze', response_json)
        self.assertEqual(response_json['can_freeze'], True)

    def test_answer_question_that_does_not_exist(self):
        pass


@override_settings(ROOT_URLCONF=test_urlconf)
class TestPublicSessionEndpointAnswerAttachmentFlow(ValidateJsonSchemaMixin, APITestCase):
    base_endpoint = '/public/qa/sessions/'

    def setUp(self):
        # sketch:
        #    q1 <- first question (PlainText)
        #    |
        #    q2 <- second question (Image)
        self.q1 = QuestionFactory.create(analysis_key='q1', label='q1', short_label='q1', required=True)
        self.q2 = QuestionFactory.create(analysis_key='q2', label='q2', short_label='q2', field_type='image',
                                         required=True, multiple_answers_allowed=False)
        graph = QuestionGraphFactory.create(name='testgraph', first_question=self.q1)
        EdgeFactory.create(graph=graph, question=self.q1, next_question=self.q2)

        self.questionnaire = QuestionnaireFactory.create(graph=graph, name='test', flow=Questionnaire.EXTRA_PROPERTIES)

        self.session = SessionFactory(questionnaire=self.questionnaire, submit_before=None, duration=None, frozen=False)

    def test_answer_all_questions(self):
        answer_data = [{'question_uuid': str(self.q1.uuid), 'payload': 'Answer to q1'}, ]
        response = self.client.post(f'{self.base_endpoint}{self.session.uuid}/answers', data=answer_data, format='json')
        self.assertEqual(response.status_code, 200)
        response_json = response.json()

        self.assertIn('path_questions', response_json)
        self.assertEqual(len(response_json['path_questions']), 2)
        self.assertIn('path_answered_question_uuids', response_json)

        self.assertIn(str(self.q1.uuid), response_json['path_answered_question_uuids'])
        self.assertEqual(len(response_json['path_answered_question_uuids']), 1)

        self.assertIn('path_unanswered_question_uuids', response_json)
        self.assertEqual(len(response_json['path_unanswered_question_uuids']), 1)
        self.assertIn('path_validation_errors_by_uuid', response_json)
        self.assertEqual(len(response_json['path_validation_errors_by_uuid']), 0)
        self.assertIn('can_freeze', response_json)
        self.assertEqual(response_json['can_freeze'], False)

        image = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')
        data = {'question_uuid': str(self.q2.uuid), 'file': image}
        response = self.client.post(f'{self.base_endpoint}{self.session.uuid}/attachments', data=data)
        self.assertEqual(response.status_code, 201)
        response_json = response.json()

        self.assertIn('path_questions', response_json)
        self.assertEqual(len(response_json['path_questions']), 2)
        self.assertIn('path_answered_question_uuids', response_json)

        self.assertIn(str(self.q1.uuid), response_json['path_answered_question_uuids'])
        self.assertEqual(len(response_json['path_answered_question_uuids']), 2)

        self.assertIn('path_unanswered_question_uuids', response_json)
        self.assertEqual(len(response_json['path_unanswered_question_uuids']), 0)
        self.assertIn('path_validation_errors_by_uuid', response_json)
        self.assertEqual(len(response_json['path_validation_errors_by_uuid']), 0)
        self.assertIn('can_freeze', response_json)
        self.assertEqual(response_json['can_freeze'], True)

    def test_answer_question_q1_plain_text_correctly(self):
        """
        q1 is a PlainText question, so we can answer it with a string using the answers endpoint
        """
        answer_data = [{'question_uuid': str(self.q1.uuid), 'payload': 'Answer to q1'}, ]
        response = self.client.post(f'{self.base_endpoint}{self.session.uuid}/answers', data=answer_data, format='json')
        self.assertEqual(response.status_code, 200)
        response_json = response.json()

        self.assertIn('path_questions', response_json)
        self.assertEqual(len(response_json['path_questions']), 2)
        self.assertIn('path_answered_question_uuids', response_json)
        self.assertEqual(len(response_json['path_answered_question_uuids']), 1)
        self.assertIn(str(self.q1.uuid), response_json['path_answered_question_uuids'])
        self.assertIn('path_unanswered_question_uuids', response_json)
        self.assertEqual(len(response_json['path_unanswered_question_uuids']), 1)
        self.assertIn('path_validation_errors_by_uuid', response_json)
        self.assertEqual(len(response_json['path_validation_errors_by_uuid']), 0)
        self.assertIn('can_freeze', response_json)
        self.assertEqual(response_json['can_freeze'], False)

    def test_answer_question_q2_image_correctly(self):
        """
        q2 is an Image question, so we can answer it with a file using the attachments endpoint
        """
        image = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')
        answer_data = {'question_uuid': str(self.q2.uuid), 'file': image}
        response = self.client.post(f'{self.base_endpoint}{self.session.uuid}/attachments', data=answer_data)
        self.assertEqual(response.status_code, 201)
        response_json = response.json()

        self.assertIn('path_questions', response_json)
        self.assertEqual(len(response_json['path_questions']), 2)
        self.assertIn('path_answered_question_uuids', response_json)
        self.assertEqual(len(response_json['path_answered_question_uuids']), 1)
        self.assertIn(str(self.q2.uuid), response_json['path_answered_question_uuids'])
        self.assertIn('path_unanswered_question_uuids', response_json)
        self.assertEqual(len(response_json['path_unanswered_question_uuids']), 1)
        self.assertIn('path_validation_errors_by_uuid', response_json)
        self.assertEqual(len(response_json['path_validation_errors_by_uuid']), 0)
        self.assertIn('can_freeze', response_json)
        self.assertEqual(response_json['can_freeze'], False)

    def test_answer_question_q2_multiple_images_correctly(self):
        """
        q2 is an Image question which we modify to have multiple_answers_allowed=True
        """
        # modify image question to allow multiple uploads
        self.q2.multiple_answers_allowed = True
        self.q2.save()

        # upload multiple images
        image_1 = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')
        image_2 = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')

        answer_data = {'question_uuid': str(self.q2.uuid), 'file': [image_1, image_2]}
        response = self.client.post(f'{self.base_endpoint}{self.session.uuid}/attachments', data=answer_data)
        self.assertEqual(response.status_code, 201)
        response_json = response.json()

        self.assertIn('path_questions', response_json)
        self.assertEqual(len(response_json['path_questions']), 2)
        self.assertIn('path_answered_question_uuids', response_json)
        self.assertEqual(len(response_json['path_answered_question_uuids']), 1)
        self.assertIn(str(self.q2.uuid), response_json['path_answered_question_uuids'])
        self.assertIn('path_unanswered_question_uuids', response_json)
        self.assertEqual(len(response_json['path_unanswered_question_uuids']), 1)
        self.assertIn('path_validation_errors_by_uuid', response_json)
        self.assertEqual(len(response_json['path_validation_errors_by_uuid']), 0)
        self.assertIn('can_freeze', response_json)
        self.assertEqual(response_json['can_freeze'], False)

    def test_answer_question_q2_image_incorrectly_wrong_endpoint(self):
        """
        q2 is an Image question, we intentionally use the wrong endpoint to test the error handling
        """
        answer_data = [{'question_uuid': str(self.q2.uuid),
                        'payload': 'should not be answered using the answer payload'}, ]

        # Use answers instead of attachments endpoint should raise an error
        response = self.client.post(f'{self.base_endpoint}{self.session.uuid}/answers', data=answer_data, format='json')
        self.assertEqual(response.status_code, 200)
        response_json = response.json()

        self.assertIn('path_validation_errors_by_uuid', response_json)
        self.assertEqual(len(response_json['path_validation_errors_by_uuid']), 1)
        self.assertIn(str(self.q2.uuid), response_json['path_validation_errors_by_uuid'])
        self.assertEqual(response_json['path_validation_errors_by_uuid'][str(self.q2.uuid)],
                         'It is not possible to answer "Attachment" questions via this endpoint')
