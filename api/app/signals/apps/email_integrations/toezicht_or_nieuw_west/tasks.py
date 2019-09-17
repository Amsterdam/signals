from signals.apps.email_integrations.toezicht_or_nieuw_west import mail
from signals.apps.email_integrations.toezicht_or_nieuw_west.utils import is_signal_applicable
from signals.apps.signals.models import Signal
from signals.celery import app


@app.task
def send_mail_toezicht_or_nieuw_west(pk):
    try:
        signal = Signal.objects.get(pk=pk)
    except Signal.DoesNotExist:
        return
    else:
        if is_signal_applicable(signal):
            mail.send_mail(signal)
