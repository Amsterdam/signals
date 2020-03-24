from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from django.template import loader

from signals.apps.feedback.models import Feedback
from signals.apps.feedback.utils import get_feedback_urls
from signals.apps.signals import workflow


def _create_message(template_name, context={}):
    template = loader.get_template(template_name)
    message = template.render(context)
    return message


def send_mail_reporter_created(signal):
    if not signal.reporter.email:
        return None

    context = {
        'signal': signal,
        'afhandelings_text': signal.category_assignment.category.handling_message,
    }
    txt_message = _create_message('email/signal_created.txt', context=context)
    html_message = _create_message('email/signal_created.html', context=context)

    subject = f'Bedankt voor uw melding ({signal.id})'

    from_email = settings.NOREPLY
    recipient_list = [signal.reporter.email, ]

    return django_send_mail(subject=subject, message=txt_message, from_email=from_email,
                            recipient_list=recipient_list, html_message=html_message)


def send_mail_reporter_status_changed_afgehandeld(signal, status, prev_status):
    signal_is_afgehandeld = status.state == workflow.AFGEHANDELD
    if not signal_is_afgehandeld or not signal.reporter.email:
        return None

    # SIG-1619 We should not send a mail after request to repoen a "melding" /
    # Signal was closed, hence:
    if prev_status.state == workflow.VERZOEK_TOT_HEROPENEN:
        return None

    # Create the feedback instance
    feedback = Feedback.actions.request_feedback(signal)

    positive_feedback_url, negative_feedback_url = get_feedback_urls(feedback)
    context = {
        'negative_feedback_url': negative_feedback_url,
        'positive_feedback_url': positive_feedback_url,
        'signal': signal,
        'status': status,
    }
    txt_message = _create_message('email/signal_status_changed_afgehandeld.txt', context=context)
    html_message = _create_message('email/signal_status_changed_afgehandeld.html', context=context)

    subject = f'Betreft melding: {signal.id}'
    from_email = settings.NOREPLY
    recipient_list = [signal.reporter.email, ]

    return django_send_mail(subject=subject, message=txt_message, from_email=from_email,
                            recipient_list=recipient_list, html_message=html_message)


def send_mail_reporter_status_changed_split(signal, status):
    signal_split = status.state == workflow.GESPLITST
    if not signal_split or not signal.reporter.email:
        return None

    context = {'signal': signal, 'status': status}
    txt_message = _create_message('email/signal_split.txt', context=context)
    html_message = _create_message('email/signal_split.html', context=context)

    subject = f'Betreft melding: {signal.id}'
    from_email = settings.NOREPLY
    recipient_list = [signal.reporter.email, ]

    return django_send_mail(subject=subject, message=txt_message, from_email=from_email,
                            recipient_list=recipient_list, html_message=html_message)


def send_mail_reporter_status_changed_ingepland(signal, status):
    signal_in_behandeling = status.state == workflow.INGEPLAND
    if not signal_in_behandeling or not signal.reporter.email:
        return None

    context = {'signal': signal, 'status': status}
    txt_message = _create_message('email/signal_status_changed_ingepland.txt', context=context)
    html_message = _create_message('email/signal_status_changed_ingepland.html', context=context)

    subject = f'Betreft melding: {signal.id}'
    from_email = settings.NOREPLY
    recipient_list = [signal.reporter.email, ]

    return django_send_mail(subject=subject, message=txt_message, from_email=from_email,
                            recipient_list=recipient_list, html_message=html_message)


def send_mail_reporter_status_changed_heropend(signal, status):
    signal_heropend = status.state == workflow.HEROPEND
    if not signal_heropend or not signal.reporter.email:
        return None

    context = {'signal': signal, 'status': status}
    txt_message = _create_message('email/signal_status_changed_heropend.txt', context=context)
    html_message = _create_message('email/signal_status_changed_heropend.html', context=context)

    subject = f'Betreft melding: {signal.id}'
    from_email = settings.NOREPLY
    recipient_list = [signal.reporter.email, ]

    return django_send_mail(subject=subject, message=txt_message, from_email=from_email,
                            recipient_list=recipient_list, html_message=html_message)
