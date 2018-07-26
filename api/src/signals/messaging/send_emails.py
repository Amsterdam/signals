import re

import pytz
from django.core.mail import send_mail
from django.template import loader
from django.utils import timezone

from signals import settings
from signals.messaging.categories import get_afhandeling_text
from signals.models import AFGEHANDELD, GEANNULEERD, STADSDELEN
from signals.settings import EMAIL_INTEGRATION_ADDRESS, \
    EMAIL_INTEGRATION_ELIGIBLE_MAIN_CATEGORIES, \
    EMAIL_INTEGRATION_ELIGIBLE_SUB_CATEGORIES

NOREPLY = 'noreply@meldingen.amsterdam.nl'


## Todo: fetch PDF and attach to message?


def get_valid_email(signal):
    email_valid = r'[^@]+@[^@]+\.[^@]+'
    if signal.reporter and signal.reporter.email and re.match(email_valid,
                                                              signal.reporter.email):
        return signal.reporter.email
    else:
        return None


def get_incident_date_string(dt):
    local_dt = timezone.localtime(dt, pytz.timezone('Europe/Amsterdam'))
    week_days = (
    'Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', 'Zaterdag',
    'Zondag')
    return week_days[local_dt.weekday()] + local_dt.strftime(" %d-%m-%Y, %H:%M")


# TODO: If the image has to be attached to the e-mail, we have to postpone
#       the e-mail till the image has been uploaded. Then there has to be
#       some kind of delay after creating the the signal before sending the
#       e-mail
def handle_create_signal(signal):
    if settings.TESTING or not settings.RABBITMQ_HOST:
        return
    email = get_valid_email(signal)
    if email:

        context = {
            'signal_id': signal.id,
            'text': signal.text,
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
        template = loader.get_template('melding_bevestiging.txt')
        body = template.render(context)
        subject = f"Bedankt voor uw melding ({signal.id})"
        to = signal.reporter.email
        send_mail(
            subject,
            body,
            NOREPLY,
            (to,),
            fail_silently=False,
        )

    sc = signal.category
    sl = signal.location
    sr = signal.reporter

    if EMAIL_INTEGRATION_ADDRESS \
            and sc.main in EMAIL_INTEGRATION_ELIGIBLE_MAIN_CATEGORIES \
            and sc.sub in EMAIL_INTEGRATION_ELIGIBLE_SUB_CATEGORIES:

        context = {
            'signal_id': signal.id,
            'address_text': sl.address_text,
            'stadsdeel': STADSDELEN[sl.stadsdeel] if sl.stadsdeel else "n/a",
            'category': sc.main + " - " + sc.sub,
            'category_main': sc.main,
            'category_sub': sc.sub,
            'text': signal.text,
            'text_extra': signal.text_extra,
            'extra_properties': signal.extra_properties,
            'email': sr.email,
            'incident_date_start': get_incident_date_string(
                signal.incident_date_start)
        }

        template = loader.get_template('new_signal_integration_message.json')
        send_mail(
            subject="email",
            message=template.render(context),
            from_email=NOREPLY,
            recipient_list=(EMAIL_INTEGRATION_ADDRESS,),
            fail_silently=False
        )


def handle_status_change(signal, previous_status):
    if settings.TESTING or not settings.RABBITMQ_HOST:
        return
    if signal.status.state in (AFGEHANDELD, GEANNULEERD) and previous_status.state not in (AFGEHANDELD, GEANNULEERD):
        email = get_valid_email(signal)
        if email:
            context = {
                'signal_id': signal.id,
                'resultaat': 'afgehandeld' if signal.status.state == AFGEHANDELD else 'gannuleerd',
                'address_text': signal.location.address_text,
                'stadsdeel': signal.location.stadsdeel,
                'category': signal.category,
                'text': signal.text
            }

            ss = signal.status
            if ss.extra_properties and 'resultaat_text' in ss.extra_properties:
                context['resultaat_text'] = ss.extra_properties['resultaat_text']

            template = loader.get_template('melding_gereed.txt')
            body = template.render(context)
            subject = f"Betreft melding : {signal.id}"
            to = signal.reporter.email
            send_mail(
                subject,
                body,
                NOREPLY,
                (to,),
                fail_silently=False,
            )
