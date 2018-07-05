import re
import logging
from django.core.mail import send_mail
from django.template import loader

from signals import settings
from signals.models import AFGEHANDELD, GEANNULEERD

log = logging.getLogger(__name__)

def get_valid_email(signal):
    email_valid = r'[^@]+@[^@]+\.[^@]+'
    if signal.reporter and signal.reporter.email and re.match(email_valid, signal.reporter.email):
        return signal.reporter.email
    else:
        return None


def handle_create_signal(signal):
    if not settings.EMAIL_HOST:
        return
    email = get_valid_email(signal)
    if email:
        context = {
            'signal_id': signal.signal_id,
            'afhandelings_termijn': "onbekende termijn",
            'text': signal.text
        }
        template = loader.get_template('melding_bevestiging.txt')
        body = template.render(context)
        subject = f"Nieuwe melding : {signal.signal_id}"
        to = signal.reporter.email
        from1 = "do_not_reply@amsterdam.nl"
        result = send_mail(
            subject,
            body,
            from1,
            (to,),
            fail_silently=False,
        )
        #$ log.info("Email result: ", result)



def handle_status_change(signal, previous_status):
    if not settings.EMAIL_HOST:
        return
    if signal.status.state in (AFGEHANDELD, GEANNULEERD) and previous_status.state not in (AFGEHANDELD, GEANNULEERD):
        email = get_valid_email(signal)
        if email:
            context = {
                'signal_id': signal.signal_id,
                'resultaat': 'afgehandeld' if signal.status.state == AFGEHANDELD else 'gannuleerd'
            }
            if signal.status.extra_properties and 'resultaat_text' in signal.status.extra_properties:
                context['resultaat_text'] = signal.status.extra_properties['resultaat_text']
            template = loader.get_template('melding_gereed.txt')
            body = template.render(context)
            subject = f"Betreft melding : {signal.signal_id}"
            to = signal.reporter.email
            from1 = "do_not_reply@amsterdam.nl"
            send_mail(
                subject,
                body,
                from1,
                (to,),
                fail_silently=False,
            )