# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils.timezone import now

from signals.apps.questionnaires.app_settings import FORWARD_TO_EXTERNAL_DAYS_OPEN
from signals.apps.questionnaires.exceptions import (
    CannotFreeze,
    MissingEmail,
    SessionInvalidated,
    WrongFlow,
    WrongState,
)
from signals.apps.questionnaires.models import (
    Answer,
    AttachedSection,
    Edge,
    IllustratedText,
    Question,
    QuestionGraph,
    Questionnaire,
    Session
)
from signals.apps.questionnaires.services.session import SessionService
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal, Status
from signals.apps.signals.utils.location import AddressFormatter

logger = logging.getLogger(__name__)


def _get_description_of_location(location):
    if location.address and isinstance(location.address, dict):
        # openbare_ruimte huisnummerhuisletter-huisummer_toevoeging, postcode woonplaats
        address_formatter = AddressFormatter(address=location.address)
        return f'{address_formatter.format("O hlT")}, {address_formatter.format("P W")}'

    return f'Locatie is gepind op de kaart\n{location.geometrie[0]}, {location.geometrie[1]}'


def _copy_attachments_to_attached_files(signal, attached_section):
    """
    Attach copied Signal attachments to AttachedSection.
    """
    for attachment in signal.attachments.all():
        pass  # copy attachment file to AttachedFile / StoredFile models


def create_session_for_forward_to_external(signal):
    """
    Create Question, Questionnaire, and Session for "forward to external" flow.
    """
    if signal.status.state != workflow.DOORZETTEN_NAAR_EXTERN:
        msg = f'Signal {signal.id} is not in state DOORZETTEN_NAAR_EXTERN'
        raise WrongState(msg)

    if not signal.status.email_override:
        msg = f'Signal {signal.id} last status DOORZETTEN_NAAR_EXTERN must have non-null email_override.'
        raise MissingEmail(msg)

    with transaction.atomic():
        ilt = IllustratedText.objects.create(title='Melding reactie')
        section1 = AttachedSection.objects.create(
            header='De melding',
            text=(f'Nummer: {signal.get_id_display()}\n'
                  f'Plaats: {_get_description_of_location(signal.location)}'
            ),
            illustrated_text=ilt,
        )
        section2 = AttachedSection.objects.create(header='Omschrijving', text=signal.status.text, illustrated_text=ilt)
        ilt.set_attachedsection_order([section1.id, section2.id])

        if signal.attachments.exists():
            photo_section = AttachedSection.object.create(header="Foto's", illustrated_text=ilt, order=3)
            _copy_attachments_to_attached_files(signal, photo_section)

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
        )

        graph = QuestionGraph.objects.create(first_question=first_question)
        Edge.objects.create(graph=graph, question=first_question, next_question=photo_question)
        questionnaire = Questionnaire.objects.create(
            description=f'Vragenlijst voor naar externe doorgezette melding {signal.get_id_display()}.',
            graph=graph,
            flow=Questionnaire.FORWARD_TO_EXTERNAL,
            explanation=ilt,
        )
        session = Session.objects.create(
            submit_before=now() + timedelta(days=FORWARD_TO_EXTERNAL_DAYS_OPEN),
            duration=None,
            questionnaire=questionnaire,
            _signal=signal,
            status=signal.status,
        )

    return session


def get_forward_to_external_url(session):
    return f'{settings.FRONTEND_URL}/incident/extern/{session.uuid}'


def clean_up_forward_to_external():
    """
    Outstanding sessions must be invalidated after FORWARD_TO_EXTERNAL_DAYS_OPEN
    days with appropriate entry in history.
    """
    open_session_qs = Session.objects.filter(
        frozen=False,
        invalidated=False,
        submit_before__lt=now(),
        status__state=workflow.DOORZETTEN_NAAR_EXTERN,
    )

    count = 0
    for session in open_session_qs:
        external_user = session.status.email_override
        when = session.status.created_at.strftime('%d-%m-%Y %H:%M:%S') 
        text = f'Geen antwoord ontvangen van externe behandelaar {external_user} op vraag van {when}.'

        if session._signal.status.id == session.status.id:
            # Signal is still in state DOORZETTEN_NAAR_EXTERN, we change its
            # state with an appropriate message.
            Signal.actions.update_status({'state': workflow.VERZOEK_TOT_AFHANDELING, 'text': text}, session._signal)
        else:
            # Signal is no longer in state DOORZETTEN_NAAR_EXTERN or a new
            # request was sent, we cannot just change the state. Instead we
            # add a note.
            Signal.actions.create_note({'text': text}, session._signal)

        # We use the invalidated 
        session.invalidated = True
        session.save()
        count += 1

    return count


class ForwardToExternalSessionService(SessionService):
    def is_publicly_accessible(self):
        # Check general access rules.
        super().is_publicly_accessible()

        # Check forward to external flow specific rules
        signal = self.session._signal
        status = self.session.status

        # We need a reference to a Signal and a status update to FORWARD_TO_EXTERNAL
        if signal is None:
            msg = f'Session {self.session.uuid} is not associated with a Signal.'
            logger.warning(msg, stack_info=True)
            raise SessionInvalidated(msg)

        if status is None:
            msg = f'Session {self.session.uuid} is not associated with a Status update.'
            logger.warning(msg, stack_info=True)
            raise SessionInvalidated(msg)

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

        answer = self.answers_by_analysis_key['reaction']  # CHECK THAT THIS IS A STRING AND NOT AN Answer isntance
        text = f'Toelichting door behandelaar ({self.session.status.email_override}): {answer.payload}'

        Signal.actions.update_status({'text': text, 'state': workflow.VERZOEK_TOT_AFHANDELING}, self.session._signal)
