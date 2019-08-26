from django.contrib.gis.db import models

from signals.apps.signals.models.category import Category


class ServiceLevelAgreement(models.Model):
    CALENDAR_DAY = True
    WORK_DAY = False
    USE_CALENDAR_DAY_CHOICES = [
        (CALENDAR_DAY, 'Kalender dagen'),
        (WORK_DAY, 'Werk dagen')
    ]
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    n_days = models.IntegerField()
    use_calendar_days = models.BooleanField(
        default=False, choices=USE_CALENDAR_DAY_CHOICES)
