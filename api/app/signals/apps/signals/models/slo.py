from django.contrib.gis.db import models

from signals.apps.signals.models.category import Category


class ServiceLevelObjective(models.Model):
    CALENDAR_DAY = True
    WORK_DAY = False
    USE_CALENDAR_DAY_CHOICES = [
        (CALENDAR_DAY, 'Kalender dagen'),
        (WORK_DAY, 'Werk dagen')
    ]
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='slo')
    n_days = models.IntegerField()
    use_calendar_days = models.BooleanField(default=False, choices=USE_CALENDAR_DAY_CHOICES)

    created_at = models.DateTimeField(editable=False, auto_now_add=True, null=True, blank=True)
    created_by = models.EmailField(null=True, blank=True)
