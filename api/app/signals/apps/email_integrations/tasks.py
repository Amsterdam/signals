from signals.celery import app

from signals.apps.email_integrations.integrations import apptimize, flex_horeca, default
from signals.apps.signals.models import Signal, Status


@app.task
def send_mail_reporter(pk):
    signal = Signal.objects.get(pk=pk)
    default.send_mail_reporter(signal)


@app.task
def send_mail_status_change(status_pk, prev_status_pk):
    status = Status.objects.get(pk=status_pk)
    prev_status = Status.objects.get(pk=prev_status_pk)
    default.send_mail_status_change(status, prev_status)


@app.task
def send_mail_apptimize(pk):
    signal = Signal.objects.get(pk=pk)
    apptimize.send_mail(signal)


@app.task
def send_mail_flex_horeca(pk):
    signal = Signal.objects.get(pk=pk)
    flex_horeca.send_mail(signal)

