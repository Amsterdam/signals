"""
E-mail integration for 'core' Signal behaviour.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader

from signals.apps.email_integrations.messages import ALL_AFHANDELING_TEXT
from signals.apps.signals import workflow


def send_mail_reporter_created(signal):
    """Send a notification e-mail to the reporter about initial create of the given `Signal` object.

    :param signal: Signal object
    :returns: number of successfully send messages or None
    """
    if not signal.reporter.email:
        return None

    subject = f'Bedankt voor uw melding ({signal.id})'
    message = create_initial_create_notification_message(signal)
    to = signal.reporter.email

    return send_mail(subject, message, settings.NOREPLY, (to, ))


def create_initial_create_notification_message(signal):
    """Create e-mail body message about initial create of the given `Signal` object.

    :param signal: Signal object
    :returns: message (str)
    """
    context = {
        'signal': signal,
        'afhandelings_text': (
            ALL_AFHANDELING_TEXT[signal.category_assignment.category.handling]
        ),
    }
    template = loader.get_template('email/signal_created.txt')
    message = template.render(context)
    return message


def send_mail_reporter_status_changed_afgehandeld(signal, status):
    """Send a notification e-mail to the reporter about status change of the given `Signal` object.

    :param signal: Signal object
    :param status: Status object
    :returns: number of successfully send messages or None
    """
    signal_is_afgehandeld = status.state == workflow.AFGEHANDELD
    if not signal_is_afgehandeld or not signal.reporter.email:
        return None

    subject = f'Betreft melding: {signal.id}'
    txt_message = create_status_change_notification_message(signal, status)
    html_message = create_status_change_notification_html_message(signal, status)
    to = signal.reporter.email

    return send_mail(subject, txt_message, settings.NOREPLY, (to, ), html_message=html_message)


def create_status_change_notification_message(signal, status):
    """Create e-mail body message about status change of the given `Signal` object.

    :param signal: Signal object
    :param status: Status object
    :returns: message (str)
    """
    context = {
        'signal': signal,
        'status': status,
    }
    template = loader.get_template('email/signal_status_changed_afgehandeld.txt')
    message = template.render(context)
    return message


def create_status_change_notification_html_message(signal, status):
    """Create e-mail body message about status change of the given `Signal` object.

    :param signal: Signal object
    :param status: Status object
    :returns: message (str)
    """
    context = {
        'signal': signal,
        'status': status,
    }
    template = loader.get_template('email/signal_status_changed_afgehandeld.html')
    message = template.render(context)
    return message


def send_mail_reporter_status_changed_split(signal, status):
    """Notify reporter that `Signal` was split into several children.

    :param signal: Signal object
    :param status: Status object
    :returns: number of successfully send messages or None
    """
    signal_split = status.state == workflow.GESPLITST

    if not signal_split or not signal.reporter.email:
        return None

    subject = f'Betreft melding: {signal.id}'
    txt_message = create_status_change_notification_split(signal, status)
    to = signal.reporter.email

    return send_mail(subject, txt_message, settings.NOREPLY, (to, ))


def create_status_change_notification_split(signal, status):
    """Create e-mail body message about status change to split of the given `Signal` object.

    :param signal: Signal object
    :param status: Status object
    :returns: message (str)
    """
    context = {
        'signal': signal,
        'status': status,
    }

    template = loader.get_template('email/signal_status_changed_split.txt')
    message = template.render(context)
    return message
