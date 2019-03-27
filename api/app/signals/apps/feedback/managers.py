from django.contrib.gis.db import models


class FeedbackManager(models.Manager):
    def request_feedback(self, signal):
        from .models import Feedback

        feedback = Feedback.objects.create(**{
            '_signal': signal,
        })

        return feedback
