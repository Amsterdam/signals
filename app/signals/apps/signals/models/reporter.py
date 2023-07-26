# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from typing import Final

from django.contrib.gis.db import models
from django.core.exceptions import MultipleObjectsReturned
from django_fsm import ConcurrentTransitionMixin, FSMField, transition

from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.renderers.email_template_renderer import EmailTemplateRenderer
from signals.apps.signals.models.mixins import CreatedUpdatedModel
from signals.apps.signals.tokens.token_generator import TokenGenerator


class Reporter(ConcurrentTransitionMixin, CreatedUpdatedModel):
    """
    Privacy-sensitive information on reporter.

    This information will be anonymized after X time
    """
    REPORTER_STATE_NEW: Final = 'new'
    REPORTER_STATE_VERIFICATION_EMAIL_SENT: Final = 'verification_email_sent'
    REPORTER_STATE_CANCELLED: Final = 'cancelled'
    REPORTER_STATE_APPROVED: Final = 'approved'
    REPORTER_STATES = (
        (REPORTER_STATE_NEW, 'New'),
        (REPORTER_STATE_VERIFICATION_EMAIL_SENT, 'Verification email sent'),
        (REPORTER_STATE_CANCELLED, 'Cancelled'),
        (REPORTER_STATE_APPROVED, 'Approved'),
    )

    _signal = models.ForeignKey(
        'signals.Signal', related_name='reporters',
        null=False, on_delete=models.CASCADE
    )

    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=17, blank=True, null=True)

    email_anonymized = models.BooleanField(default=False)
    phone_anonymized = models.BooleanField(default=False)

    sharing_allowed = models.BooleanField(default=False)

    # State managed through Django-FSM, used when a new reporter is added to a signal
    state = FSMField(default=REPORTER_STATE_NEW, protected=True)

    email_verification_token = models.CharField(max_length=120, null=True, db_index=True)
    email_verification_token_expires = models.DateTimeField(null=True)
    email_verified = models.BooleanField(default=False)

    class Meta:
        permissions = (
            ('sia_can_view_contact_details', 'Inzien van contactgegevens melder (in melding)'),
        )

    @property
    def is_anonymized(self) -> bool:
        """
        Checks if an anonymous reporter is anonymized?
        """
        return self.is_anonymous and (self.email_anonymized or self.phone_anonymized)

    @property
    def is_anonymous(self) -> bool:
        """
        Checks if a reporter is anonymous
        """
        return not self.email and not self.phone

    def is_not_original(self) -> bool:
        """
        Used as state machine transition condition to check if the reporter within this
        context is not the original (first) reporter.
        """
        try:
            Reporter.objects.filter(_signal=self._signal).get()
        except MultipleObjectsReturned:
            return True

        return False

    def includes_email(self) -> bool:
        """
        Used as state machine transition condition to check if email is available.
        """
        return self.email is not None and self.email != ''

    def email_changed(self) -> bool:
        """
        Used as state machine transition condition to check if email changed from the
        previous approved reporter.
        """
        return self._signal.reporter.email != self.email

    def is_approvable(self) -> bool:
        """
        Used as state machine transition condition to check if transition can be approved.
        This is less specific than the other condition methods, because there are a few "or"
        conditions.
        """
        if self.state == self.REPORTER_STATE_VERIFICATION_EMAIL_SENT:
            return self.is_email_verified()

        if not self.is_not_original():
            return True

        if self._signal.reporter.phone != self.phone:
            if self.email is None or self.email == self._signal.reporter.email:
                return True

        return False

    def is_email_verified(self) -> bool:
        """
        Used as state machine transition condition to check if the email address is verified.
        """
        return self.email_verified

    @transition(
        field='state',
        source=(REPORTER_STATE_NEW, REPORTER_STATE_VERIFICATION_EMAIL_SENT, ),
        target=REPORTER_STATE_CANCELLED,
        conditions=(is_not_original, ),
    )
    def cancel(self) -> None:
        """
        Use this method to transition to the 'cancelled' state.
        """
        self.email_verification_token = None

    @transition(
        field='state',
        source=(REPORTER_STATE_NEW, ),
        target=REPORTER_STATE_VERIFICATION_EMAIL_SENT,
        conditions=(includes_email, is_not_original, email_changed),
    )
    def verify_email(self) -> None:
        """
        Use this method to transition to the 'verification_email_sent' state.
        """
        # Import here to prevent circular import
        from signals.apps.email_integrations.email_verification.reporter_mailer import (
            ReporterMailer
        )
        from signals.apps.email_integrations.email_verification.reporter_verification import (
            ReporterVerifier
        )

        mail_reporter = ReporterMailer(EmailTemplateRenderer())

        # Let the current reporter know that a change was requested
        current_reporter = self._signal.reporter
        if current_reporter.email is not None and current_reporter.email != '':
            mail_reporter(current_reporter, EmailTemplate.NOTIFY_CURRENT_REPORTER)

        # Send the verification email to the new reporter
        verify = ReporterVerifier(mail_reporter, TokenGenerator())
        verify(self)

    @transition(
        field='state',
        source=(REPORTER_STATE_NEW, REPORTER_STATE_VERIFICATION_EMAIL_SENT, ),
        target=REPORTER_STATE_APPROVED,
        conditions=(is_approvable, )
    )
    def approve(self) -> None:
        """
        Use this method to transition to the 'approved' state.
        """

    def anonymize(self, always_call_save: bool = False) -> None:
        call_save = False
        if not self.email_anonymized and self.email:
            self.email_anonymized = True
            call_save = True

        if not self.phone_anonymized and self.phone:
            self.phone_anonymized = True
            call_save = True

        if call_save or always_call_save:
            self.save()

    def save(self, *args, **kwargs) -> None:
        """
        Make sure that the email and phone are set to none while saving the Reporter
        """
        if self.email_anonymized:
            self.email = None

        if self.phone_anonymized:
            self.phone = None

        super().save(*args, **kwargs)
