from django.contrib.gis.db import models
from django.core.exceptions import ValidationError

from signals.apps.reporting.indicators import INDICATOR_ROUTES

# BEFORE (created_at < end)
# IN (created_at >= begin and created_at < end)
# P_<SOMETHING> percentage of something
# N_<SOMETHING> count of something

KNOWN_INDICATORS = list(INDICATOR_ROUTES.keys())
# Indicators can be compound indicators ... !!! (complication for later)


class ReportIndicator(models.Model):
    report = models.ForeignKey(
        'reporting.ReportDefinition', null=False, on_delete=models.CASCADE)
    code = models.CharField(max_length=16)

    def clean(self):
        if self.code not in KNOWN_INDICATORS:
            error_msg = f'Unknown variable code: {self.code}'
            raise ValidationError({'code': error_msg})

    def save(self, *args, **kwargs):
        self.full_clean()
        super(ReportIndicator, self).save(*args, **kwargs)
