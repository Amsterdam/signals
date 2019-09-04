from django.contrib.gis.db import models
from django.core.exceptions import ValidationError

from signals.apps.reporting.indicators import INDICATOR_ROUTES

# Some naming conventions:
# P_<SOMETHING> percentage of something
# N_<SOMETHING> count of something

KNOWN_INDICATORS = list(INDICATOR_ROUTES.keys())
# Indicators can be compound indicators ... !!! (complication for later)


class ReportIndicator(models.Model):
    report = models.ForeignKey(
        'reporting.ReportDefinition',
        null=False,
        on_delete=models.CASCADE,
        related_name='indicators'
    )
    code = models.CharField(max_length=32)

    def clean(self):
        if self.code not in KNOWN_INDICATORS:
            error_msg = f'Unknown variable code: {self.code}'
            raise ValidationError({'code': error_msg})

    def save(self, *args, **kwargs):
        self.full_clean()
        super(ReportIndicator, self).save(*args, **kwargs)

    def derive(self, begin, end, category, area):
        # TODO: check that we are saved to DB (else possibly invalid indicator code)
        indicator = INDICATOR_ROUTES[self.code]
        return indicator().derive(begin, end, category, area)
