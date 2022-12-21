# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals.workflow import DOORGEZET_NAAR_EXTERN


class ForwardToExternalRule(AbstractRule):
    def validate(self, signal, status):
        """
        Run all validation

        - The status state must be DOORGEZET_NAAR_EXTERN
        - The status email override must be set

        Note: we are not using the baseclass validate method because it hardcodes a number of checks for mails to
        reporters. These checks are not relevant here.
        """
        return self._validate_status(status) and self._validate_status_email_override(status)

    def _validate_status(self, status):
        """
        Validate that the status is DOORGEZET_NAAR_EXTERN
        """
        return status.state == DOORGEZET_NAAR_EXTERN

    def _validate_status_email_override(self, status):
        """
        Forwarded to external flow needs an email_override to be set and valid
        """
        try:
            validate_email(status.email_override)
        except ValidationError:
            return False
        return True
