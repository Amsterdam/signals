"""
E-mail integration for 'default' Signal actions.
"""
import logging
import re

import pytz
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
from django.utils import timezone

from signals.apps.signals.models import AFGEHANDELD
from signals.settings.categories import get_afhandeling_text

LOG = logging.getLogger()


# TODO: fetch PDF and attach to message?


def get_valid_email(signal):
    email_valid = r'[^@]+@[^@]+\.[^@]+'
    if signal.reporter and signal.reporter.email and re.match(email_valid, signal.reporter.email):
        return signal.reporter.email
    else:
        return None


def get_incident_date_string(dt):
    local_dt = timezone.localtime(dt, pytz.timezone('Europe/Amsterdam'))
    week_days = ('Maandag', 'Dinsdag', 'Woensdag', 'Donderdag',
                 'Vrijdag', 'Zaterdag', 'Zondag')
    return week_days[local_dt.weekday()] + local_dt.strftime(" %d-%m-%Y, %H:%M")


# TODO: If the image has to be attached to the e-mail, we have to postpone
#       the e-mail till the image has been uploaded. Then there has to be
#       some kind of delay after creating the the signal before sending the
#       e-mail
def send_mail_reporter(signal):
    LOG.info('Handling create signal')
    email = get_valid_email(signal)
    LOG.debug('Valid email: ' + str(email))
    if email:
        LOG.debug('Trying to compose message')
        context = {
            'signal_id': signal.id,
            'text': signal.text,
            'subcategory': signal.category.sub,
            'afhandelings_text': get_afhandeling_text(signal.category.sub),
            'address_text': signal.location.address_text,
            'incident_date_start': get_incident_date_string(
                signal.incident_date_start),
            'text_extra': signal.text_extra,
            'extra_properties': signal.extra_properties,
            'email': signal.reporter.email,
        }

        if signal.reporter.phone:
            context['phone'] = signal.reporter.phone
        template = loader.get_template('templates/email/melding_bevestiging.txt')
        body = template.render(context)
        subject = f"Bedankt voor uw melding ({signal.id})"
        to = signal.reporter.email

        LOG.info('Sending message: ' + subject)
        send_mail(
            subject,
            body,
            settings.NOREPLY,
            (to,),
            fail_silently=False,
        )


def send_mail_status_change(status, previous_status):
    signal = status.signal

    LOG.info('Handling status change of signal')
    LOG.debug('Signal %s changed to state: %s from %s',
              str(signal.id),
              str(signal.status.state),
              str(previous_status.state) if previous_status else '')

    signal_is_afgehandeld = signal.status.state in (AFGEHANDELD, )
    previous_signal_is_not_afgehandeld = (previous_status and
                                          previous_status.state not in (AFGEHANDELD, ))
    if signal_is_afgehandeld and previous_signal_is_not_afgehandeld and signal.category:

        LOG.debug('Rendering template')
        email = get_valid_email(signal)
        if email:
            context = {
                'signal_id': signal.id,
                'resultaat': 'afgehandeld' if signal.status.state == AFGEHANDELD else 'geannuleerd',
                'location': signal.location,
                'subcategory': signal.category.sub,
                'maincategory': signal.category.main,
                'text': signal.text
            }

            ss = signal.status
            if ss.text:
                context['status_text'] = ss.text

            if ss.extra_properties and 'resultaat_text' in ss.extra_properties:
                context['resultaat_text'] = ss.extra_properties['resultaat_text']

            template = loader.get_template('email/melding_gereed.txt')
            body = template.render(context)
            subject = f"Betreft melding : {signal.id}"
            to = signal.reporter.email

            LOG.debug('Sending email')
            send_mail(
                subject,
                body,
                settings.NOREPLY,
                (to,),
                fail_silently=False,
            )
