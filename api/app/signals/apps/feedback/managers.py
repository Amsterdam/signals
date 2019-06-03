import logging

from django.contrib.gis.db import models

logger = logging.getLogger(__name__)


class FeedbackManager(models.Manager):
    def request_feedback(self, signal):
        return self.create(**{'_signal': signal})
