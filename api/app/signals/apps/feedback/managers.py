from django.contrib.gis.db import models


class FeedbackManager(models.Manager):
    def request_feedback(self, signal):
        return self.create(**{'_signal': signal})
