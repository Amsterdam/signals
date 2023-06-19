# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.contrib.gis.db import models
from django.core.exceptions import MultipleObjectsReturned
from django_fsm import ConcurrentTransitionMixin, FSMField, transition

from signals.apps.signals.models.mixins import CreatedUpdatedModel


class Reporter(ConcurrentTransitionMixin, CreatedUpdatedModel):
    """
    Privacy sensitive information on reporter.

    This information will be anonymized after X time
    """
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
    state = FSMField(default='new', protected=True)

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

    def is_original(self) -> bool:
        """
        Used as state machine transition condition to check if the reporter within this
        context is the original (first) reporter.
        """
        return not self.is_not_original()

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

    # TODO: Don't hardcode state names
    @transition(
        field='state',
        source=('new', 'verification_email_sent', ),
        target='cancel',
        conditions=(is_not_original, ),
    )
    def cancel(self):
        """
        Use this method to transition to the 'cancelled' state.
        """
        pass

    @transition(
        field='state',
        source=('new', ),
        target='verification_email_sent',
        conditions=(includes_email, is_not_original, email_changed),
    )
    def verify_email(self):
        """
        Use this method to transition to the 'verification_email_sent' state.
        """
        pass

    @transition(field='state', source=('new', ), target='approved', conditions=(is_original, ))
    def approve(self):
        """
        Use this method to transition to the 'approved' state.
        """
        pass

    def save(self, *args, **kwargs):
        """
        Make sure that the email and phone are set to none while saving the Reporter
        """
        if self.email_anonymized:
            self.email = None

        if self.phone_anonymized:
            self.phone = None

        super().save(*args, **kwargs)
