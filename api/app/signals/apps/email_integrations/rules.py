# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from abc import ABC

from django.db.models import Q

from signals.apps.signals import workflow
from signals.apps.signals.models import Signal


class AbstractRule(ABC):
    __validate_prefix = 'validate_'

    def __call__(self, signal):
        return all([
            getattr(self, attribute)(signal)
            for attribute in dir(self)
            if callable(getattr(self, attribute)) and attribute.startswith(self.__validate_prefix)
        ])

    def validate_reporter_email(self, signal):
        """
        Validate if there is a reporter email
        """
        return signal.reporter and signal.reporter.email

    def validate_historical_data(self, signal):
        """
        SIG-2931, special case for children of split signal --- still needed for historical data
        """
        return Signal.objects.filter(id=signal.id).filter(
            Q(parent_id__isnull=True) | Q(parent__status__state__exact=workflow.GESPLITST)
        )


class SignalCreatedRule(AbstractRule):
    def validate_status(self, signal):
        """
        Validate if the status is GEMELD and that it is the first GEMELD status
        """
        return signal.status.state == workflow.GEMELD and signal.statuses.filter(state=workflow.GEMELD).count() == 1


class SignalHandledRule(AbstractRule):
    def validate_status(self, signal):
        """
        Validate if the status is AFGEHANDELD and previous state must not be VERZOEK_TOT_HEROPENEN
        """
        return signal.status.state == workflow.AFGEHANDELD and signal.statuses.exclude(
            id=signal.status_id
        ).order_by(
            '-created_at'
        ).values_list(
            'state',
            flat=True
        ).first() != workflow.VERZOEK_TOT_HEROPENEN


class SignalScheduledRule(AbstractRule):
    def validate_status(self, signal):
        """
        Validate if the status is INGEPLAND
        """
        return signal.status.state == workflow.INGEPLAND


class SignalReopenedRule(AbstractRule):
    def validate_status(self, signal):
        """
        Validate if the status is HEROPEND
        """
        return signal.status.state == workflow.HEROPEND


class SignalOptionalRule(AbstractRule):
    def validate_status(self, signal):
        """
        Validate if the status is GEMELD, AFWACHTING, BEHANDELING, ON_HOLD, VERZOEK_TOT_AFHANDELING or GEANNULEERD
        """
        return signal.status.state in [
            workflow.GEMELD,
            workflow.AFWACHTING,
            workflow.BEHANDELING,
            workflow.ON_HOLD,
            workflow.VERZOEK_TOT_AFHANDELING,
            workflow.GEANNULEERD,
        ] and signal.status.send_email


class SignalReactionRequestRule(AbstractRule):
    def validate_status(self, signal):
        """
        Validate if the status is REACTIE_GEVRAAGD
        """
        return signal.status.state == workflow.REACTIE_GEVRAAGD
