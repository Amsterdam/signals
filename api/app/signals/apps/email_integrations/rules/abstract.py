# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from abc import ABC, abstractmethod

from django.db.models import Q

from signals.apps.signals import workflow
from signals.apps.signals.models import Signal


class AbstractRule(ABC):
    def __call__(self, signal):
        return all([
            self._validate_reporter_email(signal),
            self._validate_historical_data(signal),
            self.validate(signal),
        ])

    @abstractmethod
    def validate(self, signal):
        """
        Overwrite this function in the defined Rule to add additional validation checks
        """
        pass

    def _validate_reporter_email(self, signal):
        """
        Validate if there is a reporter email
        """
        return signal.reporter and signal.reporter.email

    def _validate_historical_data(self, signal):
        """
        SIG-2931, special case for children of split signal --- still needed for historical data
        """
        return Signal.objects.filter(id=signal.id).filter(
            Q(parent_id__isnull=True) | Q(parent__status__state__exact=workflow.GESPLITST)
        )
