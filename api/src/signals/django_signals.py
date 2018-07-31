from django.db.models.signals import post_save
from django.dispatch import receiver

from signals.models import Signal


@receiver(post_save, sender=Signal)
def create_signal(sender, instance, created, **kwargs):
    print("HERE")
