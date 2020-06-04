from django.contrib.gis.db import models

from signals.apps.signals.models.mixins import CreatedUpdatedModel


class Reporter(CreatedUpdatedModel):
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

        super(Reporter, self).save(*args, **kwargs)
