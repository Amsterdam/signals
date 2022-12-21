# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
import logging
import os
from datetime import timedelta

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.timezone import now

from signals.apps.history.services.signal_log import SignalLogService
from signals.apps.questionnaires.app_settings import FORWARD_TO_EXTERNAL_DAYS_OPEN
from signals.apps.questionnaires.exceptions import (
    CannotFreeze,
    MissingEmail,
    SessionInvalidated,
    WrongFlow,
    WrongState
)
from signals.apps.questionnaires.models import (
    AttachedFile,
    AttachedSection,
    Edge,
    IllustratedText,
    Question,
    QuestionGraph,
    Questionnaire,
    Session,
    StoredFile
)
from signals.apps.questionnaires.services.session import SessionService
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal

logger = logging.getLogger(__name__)


def _copy_attachments_to_attached_files(signal, attached_section):
    """
    Attach copied Signal attachments to AttachedSection.
    """
    for attachment in signal.attachments.order_by('created_at').all():
        # copy attachment file to AttachedFile / StoredFile models
        filename = os.path.basename(attachment.file.name)
        cf = ContentFile(attachment.file.read())
        cf.name = filename

        stored_file = StoredFile.objects.create(file=cf)
        description = os.path.basename(stored_file.file.name)
        AttachedFile.objects.create(description=description, stored_file=stored_file, section=attached_section)


def create_session_for_forward_to_external(signal):
    """
    Create Question, Questionnaire, and Session for "forwarded to external" flow.
    """
    if signal.status.state != workflow.DOORGEZET_NAAR_EXTERN:
        msg = f'Signal {signal.id} is not in state DOORGEZET_NAAR_EXTERN'
        raise WrongState(msg)

    if not signal.status.email_override:
        msg = f'Signal {signal.id} last status DOORGEZET_NAAR_EXTERN must have non-null email_override.'
        raise MissingEmail(msg)

    with transaction.atomic():
        ilt = IllustratedText.objects.create(title='Melding reactie')
        section1 = AttachedSection.objects.create(
            header='De melding',
            text=f'Nummer: {signal.get_id_display()}\n',
            illustrated_text=ilt,
        )
        section2 = AttachedSection.objects.create(header='Omschrijving', text=signal.status.text, illustrated_text=ilt)

        if signal.attachments.exists():
            photo_section = AttachedSection.objects.create(header="Foto's", illustrated_text=ilt)
            _copy_attachments_to_attached_files(signal, photo_section)
            ilt.set_attachedsection_order([section1.id, section2.id, photo_section.id])
        else:
            ilt.set_attachedsection_order([section1.id, section2.id])

        first_question = Question.objects.create(
            required=True,
            field_type='plain_text',
            short_label='Reactie na afhandeling',
            label=('Kunt u omschrijven of en hoe de melding is opgepakt?\n'
                   'U mag daarbij ook een foto sturen.'),
            analysis_key='reaction',
        )
        photo_question = Question.objects.create(
            required=False,
            field_type='image',
            short_label="Foto's toevoegen",
            label='Voeg een foto toe om de situatie te verduidelijken.',
            analysis_key='photo_reaction',
            multiple_answers_allowed=True,
        )

        graph = QuestionGraph.objects.create(first_question=first_question)
        Edge.objects.create(graph=graph, question=first_question, next_question=photo_question)
        questionnaire = Questionnaire.objects.create(
            description=f'Vragenlijst voor naar externe doorgezette melding {signal.get_id_display()}.',
            graph=graph,
            flow=Questionnaire.FORWARD_TO_EXTERNAL,
            explanation=ilt,
            is_active=True,
        )
        session = Session.objects.create(
            submit_before=now() + timedelta(days=FORWARD_TO_EXTERNAL_DAYS_OPEN),
            duration=None,
            questionnaire=questionnaire,
            _signal=signal,
            _signal_status=signal.status,
            _signal_location=signal.location,
        )

    return session


def get_forward_to_external_url(session):
    return f'{settings.FRONTEND_URL}/incident/extern/{session.uuid}'


def clean_up_forward_to_external():
    """
    Outstanding sessions must be invalidated after FORWARD_TO_EXTERNAL_DAYS_OPEN
    days with appropriate entry in history.
    """
    # from signals.apps.history.models import Log
    # n_logs = Log.objects.count()

    open_session_qs = Session.objects.filter(
        frozen=False,
        invalidated=False,
        submit_before__lt=now(),
        _signal_status__state=workflow.DOORGEZET_NAAR_EXTERN,
    )

    count = 0
    for session in open_session_qs:
        # When invalidating a session we add a log entry stating we received no
        # reaction from the external party. On top of that we transition the
        # to signal state to VERZOEK_TOT_AFHANDELING if not status updates were
        # performed since forwarding to an external party.
        SignalLogService.log_external_reaction_not_received(session)
        if session._signal.status.id == session._signal_status.id:
            # Signal is still in state DOORGEZET_NAAR_EXTERN, we change its
            # state with an appropriate message.
            Signal.actions.update_status({'state': workflow.VERZOEK_TOT_AFHANDELING}, session._signal)

        # We use the invalidated property, and not frozen, because we want to
        # handle each session once and need to mark them invalidated. We cannot
        # re-use the frozen property, because that is set when a fully validated
        # session is submitted.
        session.invalidated = True
        session.save()
        count += 1

    return count


class ForwardToExternalSessionService(SessionService):
    def is_publicly_accessible(self):
        # Check general access rules.
        super().is_publicly_accessible()

        # Check forwarded to external flow specific rules
        signal = self.session._signal
        status = self.session._signal_status

        # We need a reference to a Signal and a status update to FORWARD_TO_EXTERNAL
        if signal is None:
            msg = f'Session {self.session.uuid} is not associated with a Signal.'
            logger.warning(msg, stack_info=True)
            raise SessionInvalidated(msg)

        if status is None:
            msg = f'Session {self.session.uuid} is not associated with a Status update.'
            logger.warning(msg, stack_info=True)
            raise SessionInvalidated(msg)

    def _add_history_entry_on_freeze(self):
        """
        Create a history entry on reception of answer to forwarded question.
        """
        answer = self.answers_by_analysis_key['reaction']
        signal = self.session._signal

        # Note our history entry can come in one of two forms. In both cases we
        # use the history app to add a log entry with the message (reaction) we
        # received from the external party. And on top of that if the signal
        # status was not updated after we forwarded it we create a further
        # status update to VERZOEK_TOT_AFHANDELING (without a message).
        SignalLogService.log_external_reaction_received(self.session, answer.payload)
        if self.session._signal_status == signal.status:
            Signal.actions.update_status({'state': workflow.VERZOEK_TOT_AFHANDELING}, signal)

    def _send_confirmation_mail(self):
        """
        Confirm through email the reception of answer to forwarded question.
        """
        from signals.apps.email_integrations.services import MailService

        answer = self.answers_by_analysis_key['reaction']
        signal = self.session._signal
        email_override = self.session._signal_status.email_override

        MailService.system_mail(signal=signal, action_name='forward_to_external_reaction_received',
                                reaction_text=answer.payload, email_override=email_override)

    def _copy_attachments_from_session_to_signal(self):
        """
        If external collaborator added attachments to a questionnaire these must
        show up as normal attachments attributed to the external collaborator.
        """
        from django.core.files.storage import default_storage

        from signals.apps.signals.models import Attachment

        photo_answer = self.answers_by_analysis_key.get('photo_reaction', None)
        if not photo_answer:
            return

        assert isinstance(photo_answer.payload, list)

        for attachment_payload in photo_answer.payload:
            file_path = attachment_payload['file_path']
            with default_storage.open(file_path) as f:
                cf = ContentFile(f.read())
                cf.name = os.path.basename(file_path)

            signal = self.session._signal
            email_override = self.session._signal_status.email_override
            Attachment.objects.create(_signal=signal, file=cf, created_by=email_override)

    def freeze(self, refresh=True):
        """
        Freeze self.session, FORWARD_TO_EXTERNAL business rules.
        """
        if refresh:
            self.refresh_from_db()  # Make sure cache is not stale // TODO: this can raise, deal with it

        if not self._can_freeze:
            msg = f'Session (uuid={self.session.uuid}) is not fully answered.'
            raise CannotFreeze(msg)

        if self.session.questionnaire.flow != Questionnaire.FORWARD_TO_EXTERNAL:
            msg = f'Questionnaire flow property for session {self.session.uuid} is not FORWARD_TO_EXTERNAL!'
            raise WrongFlow(msg)

        super().freeze()
        self._add_history_entry_on_freeze()
        self._send_confirmation_mail()
        self._copy_attachments_from_session_to_signal()
