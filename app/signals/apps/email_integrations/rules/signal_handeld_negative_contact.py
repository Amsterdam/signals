# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.conf import settings

from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals.models import Status
from signals.apps.signals.workflow import AFGEHANDELD, VERZOEK_TOT_HEROPENEN


class SignalHandledNegativeRule(AbstractRule):

    def _validate_status(self, status):
        """
        Run status validations for the Rule

        - The status is AFGEHANDELD
        - The previous state is VERZOEK_TOT_HEROPENEN
        - latest feed has allows_contact set True
        """

        return self._validate_status_state(status) and \
            self._validate_previous_state_VERZOEK_TOT_HEROPENEN(status) and \
            self._is_allows_contact(status)

    def _validate_status_state(self, status):
        """
        Validate that the status is AFGEHANDELD
        """
        return status.state == AFGEHANDELD

    def _validate_previous_state_VERZOEK_TOT_HEROPENEN(self, status) -> bool:
        """
        Validate that the previous state is VERZOEK_TOT_HEROPENEN
        """

        return Status.objects.filter(
            _signal_id=status._signal_id
        ).exclude(
            id=status.id
        ).order_by('-created_at').values_list(
            'state',
            flat=True
        ).first() == VERZOEK_TOT_HEROPENEN

    def _is_allows_contact(self, status) -> bool:
        """
        check if the feedback from the signal is to allow contact with the user.
        """
        try:
            return status._signal.feedback.last().allows_contact
        except AttributeError:
            # if no feedback exists return False
            return False

    def _validate(self, signal):
        return settings.FEATURE_FLAGS.get('REPORTER_MAIL_HANDLED_NEGATIVE_CONTACT_ENABLED', True)
