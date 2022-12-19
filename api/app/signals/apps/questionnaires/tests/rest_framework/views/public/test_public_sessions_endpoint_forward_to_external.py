# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
"""
Test the forwarded to external flow at REST API level.
"""
import copy
import os
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

from django.conf import settings
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import include, path
from freezegun import freeze_time
from rest_framework.test import APITestCase

from signals.apps.api.views import NamespaceView
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.services import MailService
from signals.apps.history.models import Log
from signals.apps.questionnaires.app_settings import FORWARD_TO_EXTERNAL_DAYS_OPEN
from signals.apps.questionnaires.factories import AnswerFactory
from signals.apps.questionnaires.models import Questionnaire, Session
from signals.apps.questionnaires.services.forward_to_external import (
    create_session_for_forward_to_external,
    get_forward_to_external_url
)
from signals.apps.questionnaires.tests.mixin import ValidateJsonSchemaMixin
from signals.apps.signals import workflow
from signals.apps.signals.factories import (
    SignalFactory,
    SignalFactoryValidLocation,
    SignalFactoryWithImage,
    StatusFactory
)
from signals.apps.signals.managers import SignalManager
from signals.apps.signals.models import Attachment, Note, Signal, Status
from signals.apps.signals.tests.attachment_helpers import small_gif
from signals.test.utils import SuperUserMixin

THIS_DIR = os.path.dirname(__file__)

urlpatterns = [
    path('v1/relations/', NamespaceView.as_view(), name='signal-namespace'),
    path('', include('signals.apps.questionnaires.urls')),
]


class NameSpace:
    pass


feature_flags = copy.deepcopy(settings.FEATURE_FLAGS)
feature_flags['SIGNAL_HISTORY_LOG_ENABLED'] = True


@override_settings(FEATURE_FLAGS=feature_flags)
class TriggerForwardToExternalFlowViaAPI(APITestCase, SuperUserMixin):
    QUESTION_FOR_EXTERNAL_PARTY = 'QUESTION FOR EXTERNAL PARTY'
    STATUS_UPDATE = {
        'status': {
            'email_override': 'external@example.com',
            'send_email': True,
            'text': QUESTION_FOR_EXTERNAL_PARTY,
            'state': workflow.DOORGEZET_NAAR_EXTERN
        }
    }
    SIGNAL_DETAIL_ENDPOINT = '/signals/v1/private/signals/{signal_id}'

    def setUp(self):
        self.signal = SignalFactory.create(status__state=workflow.GEMELD)
        self.signal_with_image = SignalFactoryWithImage.create(status__state=workflow.GEMELD)
        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_FORWARD_TO_EXTERNAL,
                                     title='Uw melding {{ formatted_signal_id }}'
                                           f' {EmailTemplate.SIGNAL_STATUS_CHANGED_FORWARD_TO_EXTERNAL}',
                                     body='{{ text }} {{ reaction_url }}'
                                          '{{ ORGANIZATION_NAME }}')

    @patch('signals.apps.signals.managers.update_status', autospec=True)
    def test_change_status_to_DOORGEZET_NAAR_EXTERN_django_signal_sent_correctly(self, patched_django_signal):
        """
        Trigger the DOORGEZET_NAAR_EXTERN flow via API
        """
        patched_django_signal.send_robust = MagicMock()

        # Simulate triggering DOORGEZET_NAAR_EXTERN flow via a status update:
        self.client.force_authenticate(user=self.superuser)
        url = self.SIGNAL_DETAIL_ENDPOINT.format(signal_id=self.signal.id)

        with self.captureOnCommitCallbacks(execute=True):  # make sure Django signals are sent
            response = self.client.patch(url, data=self.STATUS_UPDATE, format='json')

        # Check that we get a updated status with all the correct properties
        self.assertEqual(response.status_code, 200)
        self.signal.refresh_from_db()

        self.assertEqual(self.signal.status.text, self.STATUS_UPDATE['status']['text'])
        self.assertEqual(self.signal.status.state, workflow.DOORGEZET_NAAR_EXTERN)
        self.assertEqual(self.signal.status.email_override, self.STATUS_UPDATE['status']['email_override'])
        self.assertEqual(self.signal.status.send_email, True)

        # Check that the status_update Django signal is sent with correct arguments
        new_status = self.signal.status
        old_status = self.signal.statuses.first()
        patched_django_signal.send_robust.called_once_with(
            sender=SignalManager,
            signal_obj=self.signal,
            status=new_status,
            prev_status=old_status
        )

    def test_change_status_to_DOORGEZET_NAAR_EXTERN_no_image(self):
        n_sessions = Session.objects.count()
        n_questionnaires = Questionnaire.objects.count()
        self.assertEqual(Note.objects.count(), 0)

        # In production Django signal receivers will pick up the status changes
        # and call into the email system. Below we prepare a status update,
        # forego calling the Django signals (problematic in tests) and call into
        # the email system directly.
        Signal.actions.update_status(self.STATUS_UPDATE['status'], signal=self.signal)
        self.signal.refresh_from_db()

        self.assertEqual(len(MailService._status_actions), 9)
        MailService.status_mail(signal=self.signal.id)

        # Check that we have a Questionnaire and Session
        self.assertEqual(Session.objects.count(), n_sessions + 1)
        self.assertEqual(Questionnaire.objects.count(), n_questionnaires + 1)

        # Check that an email was sent and that its content is correct
        session = Session.objects.last()
        reaction_url = get_forward_to_external_url(session)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(EmailTemplate.SIGNAL_STATUS_CHANGED_FORWARD_TO_EXTERNAL, mail.outbox[0].subject)
        self.assertIn(reaction_url, mail.outbox[0].body)

        # Check that a note was added to the signal's history
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.last()
        self.assertEqual(note.text, 'Automatische e-mail bij doorzetten is verzonden aan externe partij.')

    def test_change_status_to_DOORGEZET_NAAR_EXTERN_with_image(self):
        n_sessions = Session.objects.count()
        n_questionnaires = Questionnaire.objects.count()
        attachment = self.signal_with_image.attachments.first()

        # In production Django signal receivers will pick up the status changes
        # and call into the email system. Below we prepare a status update,
        # forego calling the Django signals (problematic in tests) and call into
        # the email system directly.
        Signal.actions.update_status(self.STATUS_UPDATE['status'], signal=self.signal_with_image)
        self.signal_with_image.refresh_from_db()

        self.assertEqual(len(MailService._status_actions), 9)
        MailService.status_mail(signal=self.signal_with_image.id)

        # Check that we have a Questionnaire and Session
        self.assertEqual(Session.objects.count(), n_sessions + 1)
        self.assertEqual(Questionnaire.objects.count(), n_questionnaires + 1)

        # Check that an email was sent and that its content is correct
        session = Session.objects.last()
        reaction_url = get_forward_to_external_url(session)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(EmailTemplate.SIGNAL_STATUS_CHANGED_FORWARD_TO_EXTERNAL, mail.outbox[0].subject)
        self.assertIn(reaction_url, mail.outbox[0].body)

        # Check that a note was added to the signal's history
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.last()
        self.assertEqual(note.text, 'Automatische e-mail bij doorzetten is verzonden aan externe partij.')

        # Check that the attachment was copied to the questionnaire's explanations
        questionnaire = Questionnaire.objects.last()
        image_section = questionnaire.explanation.sections.last()

        ext = os.path.splitext(attachment.file.path)[1]
        self.assertEqual(image_section.files.count(), 1)
        attached_file = image_section.files.last()
        self.assertIn(ext, attached_file.description)
        self.assertIn(ext, attached_file.stored_file.file.path)


test_urlconf = NameSpace()
test_urlconf.urlpatterns = urlpatterns


@override_settings(ROOT_URLCONF=test_urlconf, FEATURE_FLAGS=feature_flags)
class TestForwardToExternalRetrieveSessionAndFillOut(ValidateJsonSchemaMixin, APITestCase):
    base_endpoint = '/public/qa/questions/'
    session_detail_endpoint = '/public/qa/sessions/{uuid}/'
    session_answers_endpoint = session_detail_endpoint + 'answers'
    session_submit_endpoint = session_detail_endpoint + 'submit'
    session_attachments_endpoint = session_detail_endpoint + 'attachments'
    question_detail_endpoint = '/public/qa/questions/{ref}'

    def setUp(self):
        self.detail_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../../json_schema/public_get_question_detail.json')
        )
        self.post_answer_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../../json_schema/public_post_question_answer_response.json')
        )
        self.session_detail_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../../json_schema/public_get_session_detail.json')
        )

        self.t_creation = datetime(2021, 10, 1, 0, 0, 0)
        seconds_open = FORWARD_TO_EXTERNAL_DAYS_OPEN * 24 * 60 * 60
        self.t_answer_in_time = self.t_creation + timedelta(seconds=seconds_open / 2)
        self.t_answer_too_late = self.t_creation + timedelta(seconds=seconds_open * 2)

        with freeze_time(self.t_creation):
            self.signal = SignalFactoryValidLocation.create(
                created_at=self.t_creation,
                status__state=workflow.DOORGEZET_NAAR_EXTERN,
                status__text='SOME QUESTION',
                status__email_override='a@example.com'
            )
            self.session = create_session_for_forward_to_external(self.signal)

        self.assertIsInstance(self.session, Session)
        self.assertEqual(self.session.questionnaire.flow, Questionnaire.FORWARD_TO_EXTERNAL)
        self.assertEqual(self.session._signal.status.state, workflow.DOORGEZET_NAAR_EXTERN)

        self.session_url = self.session_detail_endpoint.format(uuid=str(self.session.uuid))
        self.answers_url = self.session_answers_endpoint.format(uuid=str(self.session.uuid))
        self.submit_url = self.session_submit_endpoint.format(uuid=str(self.session.uuid))
        self.attachments_url = self.session_attachments_endpoint.format(uuid=str(self.session.uuid))

        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_FORWARD_TO_EXTERNAL_REACTION_RECEIVED,
                                     title='Uw reactie is ontvangen'
                                           f'{EmailTemplate.SIGNAL_FORWARD_TO_EXTERNAL_REACTION_RECEIVED}',
                                     body='{{ reaction_text }} {{ signal_id }} {{ created_at }} {{ address }}')

    @patch('signals.apps.questionnaires.rest_framework.fields.SessionPublicHyperlinkedIdentityField.get_url',
           autospec=True)
    def test_retrieve_session(self, patched_get_url):
        """
        Happy flow retrieving a non-invalidated session in time.
        """
        patched_get_url.return_value = '/some/url/'

        with freeze_time(self.t_answer_in_time):
            response = self.client.get(self.session_url)
        response_json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertJsonSchema(self.session_detail_schema, response_json)

    @patch('signals.apps.questionnaires.rest_framework.fields.SessionPublicHyperlinkedIdentityField.get_url',
           autospec=True)
    def test_retrieve_session_check_location_serialization(self, patched_get_url):
        """
        Happy flow retrieving a non-invalidated session in time.
        """
        patched_get_url.return_value = '/some/url/'
        self.session._signal_location.stadsdeel = 'A'
        self.session._signal_location.area_name = None
        self.session._signal_location.save()

        with freeze_time(self.t_answer_in_time):
            response = self.client.get(self.session_url)
        response_json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertJsonSchema(self.session_detail_schema, response_json)
        self.assertEqual(response_json['signal_snapshot']['location']['stadsdeel'], 'Centrum')
        self.assertEqual(response_json['signal_snapshot']['location']['area_name'], None)

        self.session._signal_location.stadsdeel = None
        self.session._signal_location.area_name = 'AREA NAME'
        self.session._signal_location.save()

        with freeze_time(self.t_answer_in_time):
            response = self.client.get(self.session_url)
        response_json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertJsonSchema(self.session_detail_schema, response_json)
        self.assertEqual(response_json['signal_snapshot']['location']['stadsdeel'], None)
        self.assertEqual(response_json['signal_snapshot']['location']['area_name'], 'AREA NAME')

    @patch('signals.apps.questionnaires.rest_framework.fields.SessionPublicHyperlinkedIdentityField.get_url',
           autospec=True)
    def test_retrieve_session_no_signal_means_no_signal_snapshot(self, patched_get_url):
        """
        Test to check that signal_snapshot is serialized as None when _signal is None
        """
        from signals.apps.questionnaires.factories import SessionFactory

        with freeze_time(self.t_creation):
            session = SessionFactory.create()
        session_url = self.session_detail_endpoint.format(uuid=str(session.uuid))

        with freeze_time(self.t_answer_in_time):
            response = self.client.get(session_url)
        response_json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertJsonSchema(self.session_detail_schema, response_json)
        self.assertEqual(response_json['signal_snapshot'], None)

    def test_retrieve_session_too_late(self):
        with freeze_time(self.t_answer_too_late):
            response = self.client.get(self.session_url)

        response_json = response.json()

        self.assertEqual(response.status_code, 410)
        self.assertEqual(response_json['detail'], 'Expired!')

    def test_retrieve_session_filled_out_already(self):
        """
        Retrieve session that was filled out and frozen already.
        """
        question = self.session.questionnaire.first_question
        AnswerFactory.create(
            session=self.session, question=question, payload='SOME ANSWER')
        self.session.frozen = True
        self.session.save()
        self.session.refresh_from_db()

        with freeze_time(self.t_answer_in_time):
            response = self.client.get(self.session_url)
        response_json = response.json()

        self.assertEqual(response.status_code, 410)
        self.assertEqual(response_json['detail'], 'Already used!')

    def test_retrieve_session_invalidated(self):
        self.session.invalidated = True
        self.session.save()
        self.session.refresh_from_db()

        with freeze_time(self.t_answer_in_time):
            response = self.client.get(self.session_url)
        response_json = response.json()

        self.assertEqual(response.status_code, 410)
        self.assertEqual(response_json['detail'], 'Expired!')

    @patch('signals.apps.questionnaires.rest_framework.fields.SessionPublicHyperlinkedIdentityField.get_url',
           autospec=True)
    def test_retrieve_session_forward_to_external_several_open(self, patched_get_url):
        """
        Forwarded to external flow can have several sessions open at once, all of
        which can be retrieved.
        """
        patched_get_url.return_value = '/some/url/'

        old_session_url = self.session_url
        with freeze_time(self.t_creation + timedelta(seconds=60 * 60 * 24)):
            new_status = StatusFactory.create(
                _signal=self.signal,
                state=workflow.DOORGEZET_NAAR_EXTERN,
                text='SOME SECOND QUESTION',
                email_override='b@example.com',
            )
            self.signal.status = new_status
            self.signal.save()
            new_session = create_session_for_forward_to_external(self.signal)

        new_session_url = self.session_detail_endpoint.format(uuid=str(new_session.uuid))

        with freeze_time(self.t_answer_in_time):
            response = self.client.get(old_session_url)
        self.assertEqual(response.status_code, 200)
        self.assertJsonSchema(self.session_detail_schema, response.json())

        with freeze_time(self.t_answer_in_time):
            response = self.client.get(new_session_url)
        self.assertEqual(response.status_code, 200)
        self.assertJsonSchema(self.session_detail_schema, response.json())

    @patch('signals.apps.questionnaires.rest_framework.fields.SessionPublicHyperlinkedIdentityField.get_url',
           autospec=True)
    def test_retrieve_session_signal_state_not_DOORGEZET_NAAR_EXTERN(self, patched_get_url):
        """
        Forwarded to external flow will not "close" open sessions when the status
        of the associated Signal changes to something other than
        DOORGEZET_NAAR_EXTERN.
        """
        patched_get_url.return_value = '/some/url/'

        with freeze_time(self.t_creation + timedelta(seconds=60 * 60 * 24)):
            new_status = StatusFactory.create(state=workflow.BEHANDELING, text='We are busy.')
            self.signal.status = new_status
            self.signal.save()

        with freeze_time(self.t_answer_in_time):
            response = self.client.get(self.session_url)
        self.assertEqual(response.status_code, 200)
        self.assertJsonSchema(self.session_detail_schema, response.json())

    def test_retrieve_session_does_not_exist(self):
        """
        Retrieve session which does not exist yields 404
        """
        session_uuid = uuid.uuid4()

        while Session.objects.filter(uuid=session_uuid).count() > 0:
            session_uuid = uuid.uuid4()

        url = self.session_detail_endpoint.format(uuid=session_uuid)

        with freeze_time(self.t_answer_in_time):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @patch('signals.apps.questionnaires.rest_framework.fields.SessionPublicHyperlinkedIdentityField.get_url',
           autospec=True)
    def test_retrieve_and_fill_out(self, patched_get_url):
        """
        Retrieve outstanding session and provide an answer and upload a photo.
        """
        patched_get_url.return_value = '/some/url/'
        n_attachments = self.signal.attachments.count()
        self.assertEqual(n_attachments, 0)
        n_statusses = Status.objects.count()
        n_log_entries = Log.objects.count()

        # retrieve session
        with freeze_time(self.t_answer_in_time):
            response = self.client.get(self.session_url)

        response_json = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertJsonSchema(self.session_detail_schema, response.json())

        # access questions
        self.assertEqual(len(response_json['path_questions']), 2)
        question1 = response_json['path_questions'][0]
        self.assertEqual(question1['analysis_key'], 'reaction')
        question2 = response_json['path_questions'][1]
        self.assertEqual(question2['analysis_key'], 'photo_reaction')

        # retrieve urls used in answering the questionnaire
        attachments_url = response_json['_links']['sia:post-attachments']['href']
        self.assertEqual(urlparse(attachments_url).path, self.attachments_url)
        submit_url = response_json['_links']['sia:post-submit']['href']
        self.assertEqual(urlparse(submit_url).path, self.submit_url)
        answers_url = response_json['_links']['sia:post-answers']['href']
        self.assertEqual(urlparse(answers_url).path, self.answers_url)

        # answer text question
        answer_text = 'SOME ANSWER'
        answer_payloads = [{'question_uuid': question1['uuid'], 'payload': answer_text}]  # array of answers
        with freeze_time(self.t_answer_in_time):
            response = self.client.post(answers_url, data=answer_payloads, format='json')
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertJsonSchema(self.session_detail_schema, response.json())

        # answer photo question with single uploaded file
        suf = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')
        answer_payload = {'question_uuid': question2['uuid'], 'file': suf}

        with freeze_time(self.t_answer_in_time):
            # Session attachments endpoint accepts only multipart encoded requests.
            response = self.client.post(attachments_url, data=answer_payload)
        self.assertEqual(response.status_code, 201)
        response_json = response.json()
        self.assertJsonSchema(self.session_detail_schema, response.json())

        # freeze session
        self.assertEqual(Attachment.objects.count(), 0)
        self.assertEqual(response_json['can_freeze'], True)
        with freeze_time(self.t_answer_in_time):
            response = self.client.post(submit_url)
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertJsonSchema(self.session_detail_schema, response.json())

        # Check that attachments were uploaded and correctly processed
        self.signal.refresh_from_db()
        self.assertEqual(Attachment.objects.count(), n_attachments + 1)  # uploaded image was converted to Attachment
        self.assertEqual(self.signal.attachments.count(), 1)  # uploaded image was attached to correct signals

        att = Attachment.objects.first()
        self.assertEqual(att._signal, self.signal)  # image attached to correct Signal instance
        self.assertEqual(att.created_by, self.session._signal_status.email_override)  # image correctly attributed

        # re-requesting session endpoint will fail with HTTP 410 Gone error
        with freeze_time(self.t_answer_in_time + timedelta(seconds=10)):
            response = self.client.get(self.session_url)
        self.assertEqual(response.status_code, 410)
        response_json = response.json()
        self.assertEqual(response_json['detail'], 'Already used!')

        self.assertEqual(Status.objects.count(), n_statusses + 1)
        status = Status.objects.last()
        self.assertEqual(status.state, workflow.VERZOEK_TOT_AFHANDELING)
        self.assertEqual(status.text, None)

        # Status update causes no log entry because they use Django Signals fired in on_commit callback that is
        # not active in this test. So we only get one extra log entry containing the external reaction.
        self.assertEqual(Log.objects.count(), n_log_entries + 1)
        log_entry = Log.objects.first()
        self.assertIn(answer_text, log_entry.description)

        # TODO: add support for thank-you message

    @patch('signals.apps.questionnaires.rest_framework.fields.SessionPublicHyperlinkedIdentityField.get_url',
           autospec=True)
    def test_retrieve_and_fill_out_multiple_uploaded_files(self, patched_get_url):
        """
        Retrieve outstanding session and provide an answer and upload a photo.
        """
        patched_get_url.return_value = '/some/url/'
        n_attachments = self.signal.attachments.count()
        self.assertEqual(self.signal.attachments.count(), 0)
        n_statusses = Status.objects.count()
        n_log_entries = Log.objects.count()

        # retrieve session
        with freeze_time(self.t_answer_in_time):
            response = self.client.get(self.session_url)

        response_json = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertJsonSchema(self.session_detail_schema, response.json())

        # access questions
        self.assertEqual(len(response_json['path_questions']), 2)
        question1 = response_json['path_questions'][0]
        self.assertEqual(question1['analysis_key'], 'reaction')
        question2 = response_json['path_questions'][1]
        self.assertEqual(question2['analysis_key'], 'photo_reaction')

        # retrieve urls used in answering the questionnaire
        attachments_url = response_json['_links']['sia:post-attachments']['href']
        self.assertEqual(urlparse(attachments_url).path, self.attachments_url)
        submit_url = response_json['_links']['sia:post-submit']['href']
        self.assertEqual(urlparse(submit_url).path, self.submit_url)
        answers_url = response_json['_links']['sia:post-answers']['href']
        self.assertEqual(urlparse(answers_url).path, self.answers_url)

        # answer text question
        answer_text = 'SOME ANSWER'
        answer_payloads = [{'question_uuid': question1['uuid'], 'payload': answer_text}]
        with freeze_time(self.t_answer_in_time):
            response = self.client.post(answers_url, data=answer_payloads, format='json')
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertJsonSchema(self.session_detail_schema, response.json())

        # answer photo question
        suf = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')
        suf2 = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')
        suf2.name = 'test.gif'
        answer_payload = {'question_uuid': question2['uuid'], 'file': [suf, suf2]}

        with freeze_time(self.t_answer_in_time):
            # Session attachments endpoint accepts only multipart encoded requests.
            response = self.client.post(attachments_url, data=answer_payload)
        self.assertEqual(response.status_code, 201)
        response_json = response.json()
        self.assertJsonSchema(self.session_detail_schema, response.json())

        # freeze session
        self.assertEqual(Attachment.objects.count(), 0)
        self.assertEqual(response_json['can_freeze'], True)
        with freeze_time(self.t_answer_in_time):
            response = self.client.post(submit_url)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertJsonSchema(self.session_detail_schema, response.json())

        # Check that attachments were uploaded and correctly processed
        self.signal.refresh_from_db()
        self.assertEqual(Attachment.objects.count(), n_attachments + 2)  # uploaded images were converted to Attachment
        self.assertEqual(self.signal.attachments.count(), 2)  # uploaded images were attached to correct signals

        att = Attachment.objects.first()
        self.assertEqual(att._signal, self.signal)  # image attached to correct Signal instance
        self.assertEqual(att.created_by, self.session._signal_status.email_override)  # image correctly attributed

        # re-requesting session endpoint will fail with HTTP 410 Gone error
        with freeze_time(self.t_answer_in_time + timedelta(seconds=10)):
            response = self.client.get(self.session_url)
        self.assertEqual(response.status_code, 410)
        response_json = response.json()
        self.assertEqual(response_json['detail'], 'Already used!')

        self.assertEqual(Status.objects.count(), n_statusses + 1)
        status = Status.objects.last()
        self.assertEqual(status.state, workflow.VERZOEK_TOT_AFHANDELING)
        self.assertEqual(status.text, None)

        # Status update causes no log entry because they use Django Signals fired in on_commit callback that is
        # not active in this test. So we only get one extra log entry containing the external reaction.
        self.assertEqual(Log.objects.count(), n_log_entries + 1)
        log_entry = Log.objects.first()
        self.assertIn(answer_text, log_entry.description)

        # TODO: add support for thank-you message

    @patch('signals.apps.questionnaires.rest_framework.fields.SessionPublicHyperlinkedIdentityField.get_url',
           autospec=True)
    def test_retrieve_and_fill_out_and_triggered_mail(self, patched_get_url):
        """
        Retrieve outstanding session and provide an answer check triggered email.
        """
        n_statusses = Status.objects.count()
        n_log_entries = Log.objects.count()

        patched_get_url.return_value = '/some/url/'

        # retrieve session
        with freeze_time(self.t_answer_in_time):
            response = self.client.get(self.session_url)

        response_json = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertJsonSchema(self.session_detail_schema, response.json())

        # access questions
        self.assertEqual(len(response_json['path_questions']), 2)
        text_question = response_json['path_questions'][0]
        self.assertEqual(text_question['analysis_key'], 'reaction')

        # retrieve urls used in answering the questionnaire
        submit_url = response_json['_links']['sia:post-submit']['href']
        self.assertEqual(urlparse(submit_url).path, self.submit_url)
        answers_url = response_json['_links']['sia:post-answers']['href']
        self.assertEqual(urlparse(answers_url).path, self.answers_url)

        # answer text question
        answer_text = 'SOME ANSWER'
        answer_payloads = [{'question_uuid': text_question['uuid'], 'payload': answer_text}]  # array of answers
        with freeze_time(self.t_answer_in_time):
            response = self.client.post(answers_url, data=answer_payloads, format='json')
        self.assertEqual(response.status_code, 200)
        response_json = response.json()

        # freeze session
        self.assertEqual(Attachment.objects.count(), 0)
        self.assertEqual(response_json['can_freeze'], True)
        with freeze_time(self.t_answer_in_time):
            response = self.client.post(self.submit_url)
        self.assertEqual(response.status_code, 200)

        # check that mail was triggered
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(EmailTemplate.SIGNAL_FORWARD_TO_EXTERNAL_REACTION_RECEIVED, mail.outbox[0].subject)
        self.assertIn(answer_text, mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, [self.session._signal_status.email_override])

        self.assertEqual(Status.objects.count(), n_statusses + 1)
        status = Status.objects.last()
        self.assertEqual(status.state, workflow.VERZOEK_TOT_AFHANDELING)
        self.assertEqual(status.text, None)

        self.assertEqual(Status.objects.count(), n_statusses + 1)

        # Status update causes no log entry because they use Django Signals fired in on_commit callback that is
        # not active in this test. So we only get one extra log entry containing the external reaction.
        self.assertEqual(Log.objects.count(), n_log_entries + 1)
        log_entry = Log.objects.first()
        self.assertIn(answer_text, log_entry.description)

    @patch('signals.apps.questionnaires.rest_framework.fields.SessionPublicHyperlinkedIdentityField.get_url',
           autospec=True)
    def test_retrieve_and_fill_out_after_status_update_and_triggered_mail(self, patched_get_url):
        """
        Retrieve outstanding session and provide an answer check triggered email.
        """
        Signal.actions.update_status({'text': 'STATUS GEMELD', 'state': workflow.GEMELD}, self.signal)
        n_statusses = Status.objects.count()
        n_log_entries = Log.objects.count()

        patched_get_url.return_value = '/some/url/'

        # retrieve session
        with freeze_time(self.t_answer_in_time):
            response = self.client.get(self.session_url)

        response_json = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertJsonSchema(self.session_detail_schema, response.json())

        # access questions
        self.assertEqual(len(response_json['path_questions']), 2)
        text_question = response_json['path_questions'][0]
        self.assertEqual(text_question['analysis_key'], 'reaction')

        # retrieve urls used in answering the questionnaire
        submit_url = response_json['_links']['sia:post-submit']['href']
        self.assertEqual(urlparse(submit_url).path, self.submit_url)
        answers_url = response_json['_links']['sia:post-answers']['href']
        self.assertEqual(urlparse(answers_url).path, self.answers_url)

        # answer text question
        answer_text = 'SOME ANSWER'
        answer_payloads = [{'question_uuid': text_question['uuid'], 'payload': answer_text}]  # array of answers
        with freeze_time(self.t_answer_in_time):
            response = self.client.post(answers_url, data=answer_payloads, format='json')
        self.assertEqual(response.status_code, 200)
        response_json = response.json()

        # freeze session
        self.assertEqual(Attachment.objects.count(), 0)
        self.assertEqual(response_json['can_freeze'], True)
        with freeze_time(self.t_answer_in_time):
            response = self.client.post(self.submit_url)
        self.assertEqual(response.status_code, 200)

        # check that mail was triggered
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(EmailTemplate.SIGNAL_FORWARD_TO_EXTERNAL_REACTION_RECEIVED, mail.outbox[0].subject)
        self.assertIn(answer_text, mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, [self.session._signal_status.email_override])

        # Check that we get an entry in the signal history containing the provided answer
        # (Because our signal was no longer in workflow.DOORGEZET_NAAR_EXTERN, there will
        # be no status transition to workflow.VERZOEK_TOT_AFHANDELING.)
        self.assertEqual(Status.objects.count(), n_statusses)

        # Status update causes no log entry because they use Django Signals fired in on_commit callback that is
        # not active in this test. So we only get one extra log entry containing the external reaction.
        self.assertEqual(Log.objects.count(), n_log_entries + 1)
        log_entry = Log.objects.first()
        self.assertIn(answer_text, log_entry.description)
