from django.contrib.gis.db import models

from signals.apps.signals.models.mixins import CreatedUpdatedModel


class Reporter(CreatedUpdatedModel):
    """Privacy sensitive information on reporter."""

    ANONYMOUS_EMAIL = 'anonymous@example.com'
    ANONYMOUS_PHONE = '+31000000000'

    _signal = models.ForeignKey(
        "signals.Signal", related_name="reporters",
        null=False, on_delete=models.CASCADE
    )

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=17, blank=True)

    is_anonymized = models.BooleanField(default=False)

    def anonymize(self):
        if self.email and self.email != self.ANONYMOUS_EMAIL:
            self.email = self.ANONYMOUS_EMAIL

        if self.phone and self.phone != self.ANONYMOUS_PHONE:
            self.phone = self.ANONYMOUS_PHONE

        if not self.is_anonymized:
            self.is_anonymized = True

        self.save()
