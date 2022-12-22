# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
import os
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.utils.timezone import now
from freezegun import freeze_time

from signals.apps.history.models import Log
from signals.apps.questionnaires.exceptions import CannotFreeze, MissingEmail, WrongFlow, WrongState
from signals.apps.questionnaires.factories import AnswerFactory
from signals.apps.questionnaires.models import (
    AttachedFile,
    AttachedSection,
    Edge,
    IllustratedText,
    Questionnaire,
    Session,
    StoredFile
)
from signals.apps.questionnaires.services.forward_to_external import (
    FORWARD_TO_EXTERNAL_DAYS_OPEN,
    ForwardToExternalSessionService,
    _copy_attachments_to_attached_files,
    clean_up_forward_to_external,
    create_session_for_forward_to_external,
    get_forward_to_external_url
)
from signals.apps.questionnaires.services.utils import get_session_service
from signals.apps.signals.factories import (
    SignalFactory,
    SignalFactoryValidLocation,
    SignalFactoryWithImage,
    StatusFactory
)
from signals.apps.signals.models import Attachment, Note, Signal, Status
from signals.apps.signals.workflow import DOORGEZET_NAAR_EXTERN, GEMELD, VERZOEK_TOT_AFHANDELING


class TestCreateSessionForForwardToExternal(TestCase):
    def setUp(self):
        self.signal = SignalFactoryWithImage.create()
        status_text = 'Kunt u de lantaarn vervangen?'
        new_status = Status.objects.create(
            _signal_id=self.signal.id, state=DOORGEZET_NAAR_EXTERN, text=status_text, email_override='a@example.com')
        self.signal.status = new_status
        self.signal.save()

    def test_create_session_for_forward_to_external_wrong_state(self):
        signal = SignalFactory.create(status__state=GEMELD)
        with self.assertRaises(WrongState):
            create_session_for_forward_to_external(signal)

    def test_create_session_for_forward_to_external_email_override_none(self):
        signal = SignalFactory.create(status__state=DOORGEZET_NAAR_EXTERN, status__email_override=None)
        with self.assertRaises(MissingEmail):
            create_session_for_forward_to_external(signal)

    def test_create_session_for_forward_to_external(self):
        # Check basic characteristics of created Questions, QuestionGraph, Questionnaire, and Session
        session = create_session_for_forward_to_external(self.signal)
        self.assertIsInstance(session, Session)
        self.assertEqual(session.questionnaire.flow, Questionnaire.FORWARD_TO_EXTERNAL)
        self.assertEqual(session._signal_status.email_override, 'a@example.com')

        # Check explanatory text based new Signal status
        explanation = session.questionnaire.explanation
        self.assertEqual(explanation.sections.count(), 3)

        sections = explanation.sections.all()
        self.assertEqual(sections[0].header, 'De melding')
        self.assertIn(self.signal.get_id_display(), sections[0].text)

        self.assertEqual(sections[1].header, 'Omschrijving')
        self.assertEqual(sections[1].text, self.signal.status.text)

        self.assertEqual(sections[2].header, "Foto's")
        self.assertEqual(sections[2].files.count(), 1)

        # Check question graph structure
        graph = session.questionnaire.graph
        edges = Edge.objects.filter(graph=graph)
        self.assertEqual(edges.count(), 1)

        first_question = graph.first_question
        self.assertEqual(first_question.short_label, 'Reactie na afhandeling')

        edge_to_second_question = Edge.objects.filter(graph=graph, question=first_question).first()
        second_question = edge_to_second_question.next_question
        self.assertEqual(second_question.short_label, "Foto's toevoegen")

    def test_create_session_for_forward_to_external_no_attachments(self):
        self.signal.attachments.all().delete()

        # Check basic characteristics of created Questions, QuestionGraph, Questionnaire, and Session
        session = create_session_for_forward_to_external(self.signal)
        self.assertIsInstance(session, Session)
        self.assertEqual(session.questionnaire.flow, Questionnaire.FORWARD_TO_EXTERNAL)
        self.assertEqual(session._signal_status.email_override, 'a@example.com')

        explanation = session.questionnaire.explanation

        # Check that no "Foto's" section is present:
        self.assertEqual(explanation.sections.count(), 2)
        sections = explanation.sections.all()
        self.assertEqual(sections[0].header, 'De melding')
        self.assertEqual(sections[1].header, 'Omschrijving')


class TestGetForwardToExternalUrl(TestCase):
    def test_get_forward_to_external_url(self):
        signal = SignalFactory.create(status__state=DOORGEZET_NAAR_EXTERN, status__email_override='a@example.com')
        session = create_session_for_forward_to_external(signal)

        url = f'{settings.FRONTEND_URL}/incident/extern/{session.uuid}'
        self.assertEqual(get_forward_to_external_url(session), url)


class TestForwardToExternalSessionService(TestCase):
    def setUp(self):
        self.t_session_started = now()
        self.t_session_freeze = now() + timedelta(seconds=24 * 60 * 60)

        with freeze_time(self.t_session_started):
            self.signal = SignalFactoryValidLocation.create()
            self.status_text = 'Kunt u de lantaarn vervangen?'
            new_status = Status.objects.create(
                _signal_id=self.signal.id,
                state=DOORGEZET_NAAR_EXTERN,
                text=self.status_text,
                email_override='a@example.com')
            self.signal.status = new_status
            self.signal.save()
            self.session = create_session_for_forward_to_external(self.signal)

        self.assertEqual(Note.objects.count(), 0)
        self.assertIsInstance(self.session, Session)

    def test_handle_frozen_session_FORWARD_TO_EXTERNAL_not_filled_out(self):
        service = get_session_service(self.session.uuid)
        self.assertIsInstance(service, ForwardToExternalSessionService)

        with self.assertRaises(CannotFreeze):
            service.freeze()

        # Using knowledge that only the first question is mandatory in FORWARD_TO_EXTERNAL flow questionnaire:
        AnswerFactory(session=self.session, payload='Lantaarn is gefixt!')
        service.refresh_from_db()

        service.freeze()
        self.session.refresh_from_db()

        self.assertEqual(self.session.frozen, True)

    def test_handle_frozen_session_FORWARD_TO_EXTERNAL_wrong_flow(self):
        service = get_session_service(self.session.uuid)
        self.assertIsInstance(service, ForwardToExternalSessionService)

        with freeze_time(self.t_session_freeze):
            # Using knowledge that only the first question is mandatory in FORWARD_TO_EXTERNAL flow questionnaire:
            AnswerFactory(session=self.session, payload='Lantaarn is gefixt!')

            # Change Questionnaire flow from Questionnaire.FORWARD_TO_EXTERNAL
            self.session.questionnaire.flow = Questionnaire.EXTRA_PROPERTIES
            self.session.questionnaire.save()
            service.refresh_from_db()

            self.assertEqual(service.session.questionnaire.flow, Questionnaire.EXTRA_PROPERTIES)
            with self.assertRaises(WrongFlow):
                service.freeze()

    def test_handle_frozen_session_DOORGEZET_NAAR_EXTERN(self):
        tz = ZoneInfo(settings.TIME_ZONE)
        service = get_session_service(self.session.uuid)
        self.assertIsInstance(service, ForwardToExternalSessionService)
        self.assertEqual(len(mail.outbox), 0)
        n_log = Log.objects.count()

        with freeze_time(self.t_session_freeze):
            # Using knowledge that only the first question is mandatory in forwarded to external flow:
            answer = AnswerFactory(session=self.session, payload='Lantaarn is gefixt!')
            service.refresh_from_db()

            service.freeze()
            self.signal.refresh_from_db()

            # check that we got a status update to state VERZOEK_TOT_AFHANDELING with correct properties
            question_timestamp = self.t_session_started.astimezone(tz).strftime('%d-%m-%Y %H:%M')
            self.assertEqual(self.signal.status.state, VERZOEK_TOT_AFHANDELING)
            self.assertEqual(self.signal.status.text, None)  # see log entry for reaction text (tested below)

            # Status update causes no log entry because they use Django Signals fired in on_commit callback that is
            # not active in this test. So we only get one extra log entry containing the external reaction.
            self.assertEqual(Log.objects.count(), n_log + 1)
            msg = f'Toelichting door behandelaar a@example.com op vraag van {question_timestamp} {answer.payload}'
            log_entry = Log.objects.first()
            self.assertEqual(log_entry.description, msg)

            # Check that Signalen also sent an email acknowledging the reception of an answer (without adding a
            # note to the history stating an email was sent).
            self.assertEqual(Note.objects.count(), 0)

            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, f'Melding {self.signal.get_id_display()}: reactie ontvangen')
            self.assertEqual(mail.outbox[0].to, [self.session._signal_status.email_override, ])

    def test_handle_frozen_session_DOORGEZET_NAAR_EXTERN_with_status_update(self):
        # update status after the original DOORGEZET_NAAR_EXTERN
        tz = ZoneInfo(settings.TIME_ZONE)
        delta_t = timedelta((self.t_session_freeze - self.t_session_started).seconds / 2)
        with freeze_time(self.t_session_started + delta_t):
            Signal.actions.update_status({'state': GEMELD, 'text': 'test'}, self.signal)

        # answer questionnaire / freeze session / check that note is set and no extra status update happens
        service = get_session_service(self.session.uuid)
        self.assertIsInstance(service, ForwardToExternalSessionService)
        self.assertEqual(len(mail.outbox), 0)
        n_log = Log.objects.count()

        with freeze_time(self.t_session_freeze):
            # Using knowledge that only the first question is mandatory in forwarded to external flow:
            answer = AnswerFactory(session=self.session, payload='Lantaarn is gefixt!')
            service.refresh_from_db()

            service.freeze()
            self.signal.refresh_from_db()

            # Check that we get a Note saying we received a reaction from external collaborator
            question_timestamp = self.t_session_started.astimezone(tz).strftime('%d-%m-%Y %H:%M')
            self.assertEqual(self.signal.status.state, GEMELD)

            # In the case of a status change after forwarding a signal we get no status change but we do get a log
            # entry containing the external reaction.
            self.assertEqual(Log.objects.count(), n_log + 1)
            msg = f'Toelichting door behandelaar a@example.com op vraag van {question_timestamp} {answer.payload}'
            log_entry = Log.objects.first()
            self.assertEqual(log_entry.description, msg)

            # Check that Signalen also sent an email acknowledging the reception of an answer (without adding a
            # note to the history stating an email was sent).
            self.assertEqual(Note.objects.count(), 0)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, f'Melding {self.signal.get_id_display()}: reactie ontvangen')
            self.assertEqual(mail.outbox[0].to, [self.session._signal_status.email_override, ])


class TestCleanUpForwardToExternal(TestCase):
    def test_clean_up_forward_to_external_from_DOORGEZET_NAAR_EXTERN(self):
        n_log_entries = Log.objects.count()

        with freeze_time(now() - timedelta(days=2 * FORWARD_TO_EXTERNAL_DAYS_OPEN)):
            # Five signals that were in state DOORGEZET_NAAR_EXTERN and too old to
            # still receive an update.
            signals = SignalFactory.create_batch(
                5, status__state=DOORGEZET_NAAR_EXTERN, status__email_override='a@example.com')
            for signal in signals:
                create_session_for_forward_to_external(signal)

        with freeze_time(now() - timedelta(days=FORWARD_TO_EXTERNAL_DAYS_OPEN // 2)):
            # Five signals that were in state DOORGEZET_NAAR_EXTERN and may still
            # get an update.
            SignalFactory.create_batch(
                5, status__state=DOORGEZET_NAAR_EXTERN, status__email_override='a@example.com')
            for signal in signals:
                create_session_for_forward_to_external(signal)

        self.assertEqual(Signal.objects.count(), 10)
        n_updated = clean_up_forward_to_external()

        self.assertEqual(n_updated, 5)
        closed = Signal.objects.filter(status__state=DOORGEZET_NAAR_EXTERN)
        still_open = Signal.objects.filter(status__state=VERZOEK_TOT_AFHANDELING)

        self.assertEqual(closed.count(), 5)
        self.assertEqual(still_open.count(), 5)

        self.assertEqual(Session.objects.count(), 10)
        self.assertEqual(Session.objects.filter(invalidated=True).count(), 5)

        self.assertEqual(Log.objects.count(), n_log_entries + 5)
        log = Log.objects.first()
        self.assertIn('Geen toelichting ontvangen van behandelaar', log.description)

    def test_clean_up_forward_to_external_not_from_DOORGEZET_NAAR_EXTERN(self):
        n_log_entries = Log.objects.count()

        with freeze_time(now() - timedelta(days=2 * FORWARD_TO_EXTERNAL_DAYS_OPEN)):
            # Five signals that were in state DOORGEZET_NAAR_EXTERN and too old to
            # still receive an update.
            signal = SignalFactory.create(status__state=DOORGEZET_NAAR_EXTERN, status__email_override='a@example.com')
            create_session_for_forward_to_external(signal)
            new_status = StatusFactory.create(_signal=signal)
            signal.status = new_status
            signal.save()

        with freeze_time(now() - timedelta(days=FORWARD_TO_EXTERNAL_DAYS_OPEN // 2)):
            # Five signals that were in state DOORGEZET_NAAR_EXTERN and may still
            # get an update.
            signal = SignalFactory.create(status__state=DOORGEZET_NAAR_EXTERN, status__email_override='a@example.com')
            create_session_for_forward_to_external(signal)
            new_status = StatusFactory.create(_signal=signal)
            signal.status = new_status
            signal.save()

        self.assertEqual(Signal.objects.count(), 2)
        n_updated = clean_up_forward_to_external()

        self.assertEqual(n_updated, 1)
        self.assertEqual(Signal.objects.filter(status__state=GEMELD).count(), 2)  # we want no state changes

        self.assertEqual(Session.objects.count(), 2)
        self.assertEqual(Session.objects.filter(invalidated=True).count(), 1)

        self.assertEqual(Log.objects.count(), n_log_entries + 1)
        log = Log.objects.first()
        self.assertIn('Geen toelichting ontvangen van behandelaar', log.description)


class TestCopyAttachmentsToAttachedFiles(TestCase):
    def setUp(self):
        self.signal = SignalFactoryWithImage.create(
            status__state=DOORGEZET_NAAR_EXTERN,
            status__send_email=True,
            status__email_override='external@example.com')
        self.illustrated_text = IllustratedText.objects.create(title='Title')
        self.attached_section = AttachedSection.objects.create(
            illustrated_text=self.illustrated_text,
            text='Section text',
            header='Section header')

    def test_copy_attachments_to_attached_file(self):
        self.assertEqual(Attachment.objects.count(), 1)
        self.assertEqual(StoredFile.objects.count(), 0)
        self.assertEqual(AttachedFile.objects.count(), 0)
        self.assertEqual(self.attached_section.files.count(), 0)
        _copy_attachments_to_attached_files(self.signal, self.attached_section)

        self.assertEqual(self.attached_section.files.count(), 1)
        self.assertEqual(StoredFile.objects.count(), 1)

        at = Attachment.objects.first()
        af = AttachedFile.objects.first()
        self.assertEqual(os.path.basename(at.file.name), af.description)

    def test_copy_attachments_to_attached_file_twice(self):
        self.assertEqual(Attachment.objects.count(), 1)
        self.assertEqual(StoredFile.objects.count(), 0)
        self.assertEqual(AttachedFile.objects.count(), 0)
        self.assertEqual(self.attached_section.files.count(), 0)
        _copy_attachments_to_attached_files(self.signal, self.attached_section)
        _copy_attachments_to_attached_files(self.signal, self.attached_section)

        self.assertEqual(StoredFile.objects.count(), 2)  # for now no deduplication
        self.assertEqual(AttachedFile.objects.count(), 2)
        self.assertEqual(self.attached_section.files.count(), 2)

        attached_files = list(AttachedFile.objects.all())
        fn1 = os.path.basename(attached_files[0].stored_file.file.name)
        fn2 = os.path.basename(attached_files[1].stored_file.file.name)
        self.assertNotEqual(fn1, fn2)
