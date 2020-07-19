from signals.apps.email_integrations.reporter.mail_actions import MailActions


def send_mail_reporter_created(signal, *args, **kwargs):
    mail_actions = MailActions()
    return mail_actions.apply(signal_id=signal.pk)


def send_mail_reporter_status_changed_afgehandeld(signal, *args, **kwargs):
    mail_actions = MailActions()
    return mail_actions.apply(signal_id=signal.pk)
