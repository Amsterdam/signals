import logging

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError

from signals.apps.signals import workflow
from signals.apps.signals.models.mixins import CreatedUpdatedModel

logger = logging.getLogger(__name__)


class Status(CreatedUpdatedModel):
    TARGET_API_SIGMAX = 'sigmax'
    TARGET_API_CHOICES = (
        (TARGET_API_SIGMAX, 'Sigmax (City Control)'),
    )

    _signal = models.ForeignKey('signals.Signal', related_name='statuses', on_delete=models.CASCADE)

    text = models.CharField(max_length=10000, null=True, blank=True)
    # TODO, rename field to `email` it's not a `User` it's a `email`...
    user = models.EmailField(null=True, blank=True)
    target_api = models.CharField(max_length=250, null=True, blank=True, choices=TARGET_API_CHOICES)
    state = models.CharField(max_length=20,
                             blank=True,
                             choices=workflow.STATUS_CHOICES,
                             default=workflow.GEMELD,
                             help_text='Melding status')

    # TODO, do we need this field or can we remove it?
    extern = models.BooleanField(default=False, help_text='Wel of niet status extern weergeven')

    extra_properties = JSONField(null=True, blank=True)

    class Meta:
        permissions = (
            ('push_to_sigmax', 'Doorsturen van een melding (THOR)'),  # SIG-2192
        )
        verbose_name_plural = 'Statuses'
        get_latest_by = 'datetime'
        ordering = ('created_at',)

    def __str__(self):
        return str(self.text)

    # TODO: Maybe migrate user to created_by, for now made this work-around
    @property
    def created_by(self):
        return self.user

    @created_by.setter
    def created_by(self, created_by):
        self.user = created_by

    def clean(self):
        """Validate instance.

        Most important validation is the state transition.

        :raises: ValidationError
        :returns:
        """
        errors = {}

        if self._signal.status:
            # We already have a status so let's check if the new status can be set
            current_state = self._signal.status.state
            current_state_display = self._signal.status.get_state_display()
        else:
            # No status has been set yet so we default to LEEG
            current_state = workflow.LEEG
            current_state_display = workflow.LEEG

            logger.warning('Signal #{} has status set to None'.format(self._signal.pk))

        new_state = self.state
        new_state_display = self.get_state_display()

        # Validating state transition.
        if new_state not in workflow.ALLOWED_STATUS_CHANGES[current_state]:
            error_msg = 'Invalid state transition from `{from_state}` to `{to_state}`.'.format(
                from_state=current_state_display,
                to_state=new_state_display)
            errors['state'] = ValidationError(error_msg, code='invalid')

        # Validating state "TE_VERZENDEN".
        if new_state == workflow.TE_VERZENDEN and not self.target_api:
            error_msg = 'This field is required when changing `state` to `{new_state}`.'.format(
                new_state=new_state_display)
            errors['target_api'] = ValidationError(error_msg, code='required')

        if new_state != workflow.TE_VERZENDEN and self.target_api:
            error_msg = 'This field can only be set when changing `state` to `{state}`.'.format(
                state=workflow.TE_VERZENDEN)
            errors['target_api'] = ValidationError(error_msg, code='invalid')

        # Validating text field required.
        if new_state in [workflow.AFGEHANDELD, workflow.HEROPEND] and not self.text:
            error_msg = 'This field is required when changing `state` to `{new_state}`.'.format(
                new_state=new_state_display)
            errors['text'] = ValidationError(error_msg, code='required')

        if errors:
            raise ValidationError(errors)
