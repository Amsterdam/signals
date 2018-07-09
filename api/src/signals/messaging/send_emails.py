import re
from django.core.mail import send_mail
from django.template import loader

from signals import settings
from signals.messaging.categories import get_afhandeling_text
from signals.models import AFGEHANDELD, GEANNULEERD

NOREPLY = 'noreply@meldingen.amsterdam.nl'

def get_valid_email(signal):
    email_valid = r'[^@]+@[^@]+\.[^@]+'
    if signal.reporter and signal.reporter.email and re.match(email_valid, signal.reporter.email):
        return signal.reporter.email
    else:
        return None

def get_incident_date_string(dt):
    week_days = ('Maandag', 'Disdag', 'Woensdag', 'Donderdag', 'Vrijdag', 'Zaterdag', 'Zondag')
    return week_days[dt.weekday()] + dt.strftime(" %d-%m-%Y, %H:%M")

def handle_create_signal(signal):
    if not settings.EMAIL_HOST:
        return
    email = get_valid_email(signal)
    if email:

        context = {
            'signal_id': signal.id,
            'text': signal.text,
            'afhandelings_text': get_afhandeling_text(signal.category.sub),
            'address_text': signal.location.address_text,
            'incident_date_start': get_incident_date_string(signal.incident_date_start),
            'text_extra': signal.text_extra,
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


def handle_status_change(signal, previous_status):
    if not settings.EMAIL_HOST:
        return
    if signal.status.state in (AFGEHANDELD, GEANNULEERD) and previous_status.state not in (AFGEHANDELD, GEANNULEERD):
        email = get_valid_email(signal)
        if email:
            context = {
                'signal_id': signal.id,
                'resultaat': 'afgehandeld' if signal.status.state == AFGEHANDELD else 'gannuleerd'
            }
            if signal.status.extra_properties and 'resultaat_text' in signal.status.extra_properties:
                context['resultaat_text'] = signal.status.extra_properties['resultaat_text']
            template = loader.get_template('melding_gereed.txt')
            body = template.render(context)
            subject = f"Betreft melding : {signal.signal_id}"
            to = signal.reporter.email
            send_mail(
                subject,
                body,
                NOREPLY,
                (to,),
                fail_silently=False,
            )