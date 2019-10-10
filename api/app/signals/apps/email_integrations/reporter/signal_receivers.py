from django.dispatch import receiver

from signals.apps.email_integrations.reporter import tasks
from signals.apps.signals.managers import create_initial, update_status


@receiver(create_initial, dispatch_uid='reporter_email_integrations_create_initial')
def create_initial_handler(sender, signal_obj, *args, **kwargs):
    tasks.send_mail_reporter_created.delay(pk=signal_obj.pk)


@receiver(update_status, dispatch_uid='core_email_integrations_update_status')
def update_status_handler(sender, signal_obj, status, prev_status, *args, **kwargs):
    tasks.send_mail_reporter_status_changed_afgehandeld.delay(signal_pk=signal_obj.pk,
                                                              status_pk=status.pk,
                                                              prev_status_pk=prev_status.pk)

    tasks.send_mail_reporter_status_changed_split.delay(signal_pk=signal_obj.pk,
                                                        status_pk=status.pk,
                                                        prev_status_pk=prev_status.pk)

    tasks.send_mail_reporter_status_changed_ingepland.delay(signal_pk=signal_obj.pk,
                                                            status_pk=status.pk,
                                                            prev_status_pk=prev_status.pk)

    tasks.send_mail_reporter_status_changed_heropend.delay(signal_pk=signal_obj.pk,
                                                           status_pk=status.pk,
                                                           prev_status_pk=prev_status.pk)
