# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from abc import ABC, abstractmethod

from django.db.models import Q

from signals.apps.signals import workflow
from signals.apps.signals.models import Signal


class AbstractRule(ABC):
    """
    This class must be used when creating email rule's.

    The derived class, is associated with the corresponding action. For example the SignalCreatedRule is used with the
    SignalCreatedAction to determine if it should trigger tge Signal created email to be sent.
    """
    def __call__(self, signal):
        """
        When called run all validation
        """
        return self.validate(signal, signal.status)

    def validate(self, signal, status):
        """
        Run all validations

        - The reporter email must be set
        - The Signal cannot be a child Signal OR should have the status GESPLITST
        """
        return (self._validate_reporter_email(signal) and
                self._validate_historical_data(signal) and
                self._validate_allows_contact(signal) and
                self._validate_status(status) and
                self._validate(signal))

    def _validate_reporter_email(self, signal):
        """
        Validate that the reporter email is set
        """
        value = signal.reporter and signal.reporter.email
        return value

    def _validate_historical_data(self, signal):
        """
        Validate that a Signal is not a child Signal OR that the Signal has the status GESPLITST.

        Note: Currently child signals (Dutch jargon "deelmeldingen") are used internally to track tasks that follow
              from an original signal ("hoofdmelding"). Internal tasks are never communicated to the reporter, hence no
              emails can be sent from child signals. Before that child signals were communicated to the parent signal's
              reporter. In that case the original complaint transitioned to the status GESPLITST. (See SIG-2931.)
        """
        return Signal.objects.filter(id=signal.id).filter(
            Q(parent_id__isnull=True) | Q(parent__status__state__exact=workflow.GESPLITST)
        )

    def _validate(self, signal):
        """
        Overwrite this function in the defined Rule to add additional validation checks
        """
        return True

    @abstractmethod
    def _validate_status(self, status):
        """
        overwrite this function in the defined Rule to add the additional status validation checks
        """
        return False

    def _validate_allows_contact(self, signal: Signal):
        """
        Validate if the user want to be contacted and if allows_contact on feedback is False to
        never send ANY emails to the user

        If the feature flag is False we return True to still send emails to the user.
        """
        return signal.allows_contact
