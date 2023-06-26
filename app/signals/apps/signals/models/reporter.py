# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from typing import Final

from django.contrib.gis.db import models
from django_fsm import ConcurrentTransitionMixin, FSMField

from signals.apps.signals.models.mixins import CreatedUpdatedModel


class Reporter(ConcurrentTransitionMixin, CreatedUpdatedModel):
    """
    Privacy sensitive information on reporter.

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

    class Meta:
        permissions = (
            ('sia_can_view_contact_details', 'Inzien van contactgegevens melder (in melding)'),
        )

    @property
    def is_anonymized(self):
        """
        Checks if an anonymous reporter is anonymized?
        """
        return self.is_anonymous and (self.email_anonymized or self.phone_anonymized)

    @property
    def is_anonymous(self):
        """
        Checks if a reporter is anonymous
        """
        return not self.email and not self.phone

    def anonymize(self, always_call_save=False):
        call_save = False
        if not self.email_anonymized and self.email:
            self.email_anonymized = True
            call_save = True

        if not self.phone_anonymized and self.phone:
            self.phone_anonymized = True
            call_save = True

        if call_save or always_call_save:
            self.save()

    def save(self, *args, **kwargs):
        """
        Make sure that the email and phone are set to none while saving the Reporter
        """
        if self.email_anonymized:
            self.email = None

        if self.phone_anonymized:
            self.phone = None

        super().save(*args, **kwargs)
