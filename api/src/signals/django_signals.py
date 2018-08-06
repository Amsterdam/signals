from django.db.models.signals import post_save
from django.dispatch import receiver

from signals import tasks
from signals.models import Signal


@receiver(post_save, sender=Signal)
def post_save_signal(sender, instance, created, **kwargs):
    if created:
        tasks.push_to_sigmax.delay(key=instance.id)
    tasks.send_mail_apptimize.delay(key=instance.id)
