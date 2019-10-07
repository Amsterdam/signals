from signals.apps.email_integrations.reporter import mail
from signals.apps.signals.models import Signal, Status
from signals.celery import app


@app.task
def send_mail_reporter_created(pk):
    signal = Signal.objects.get(pk=pk)
    mail.send_mail_reporter_created(signal)


@app.task
def send_mail_reporter_status_changed_split(signal_pk, status_pk, prev_status_pk):
    signal = Signal.objects.get(pk=signal_pk)
    status = Status.objects.get(pk=status_pk)
    mail.send_mail_reporter_status_changed_split(signal, status)


@app.task
def send_mail_reporter_status_changed_afgehandeld(signal_pk, status_pk, prev_status_pk):
    signal = Signal.objects.get(pk=signal_pk)
    status = Status.objects.get(pk=status_pk)
    prev_status = Status.objects.get(pk=prev_status_pk)
    mail.send_mail_reporter_status_changed_afgehandeld(signal, status, prev_status)


@app.task
def send_mail_reporter_status_changed_ingepland(signal_pk, status_pk, prev_status_pk):
    signal = Signal.objects.get(pk=signal_pk)
    status = Status.objects.get(pk=status_pk)
    mail.send_mail_reporter_status_changed_ingepland(signal, status)


@app.task
def send_mail_reporter_status_changed_heropend(signal_pk, status_pk, prev_status_pk):
    signal = Signal.objects.get(pk=signal_pk)
    status = Status.objects.get(pk=status_pk)
    mail.send_mail_reporter_status_changed_heropend(signal, status)
