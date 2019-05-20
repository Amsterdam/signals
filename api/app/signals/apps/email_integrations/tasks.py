from signals.apps.email_integrations.integrations import (
    apptimize,
    core,
    flex_horeca,
    handhaving_or_oost,
    toezicht_or_nieuw_west,
    vth_nieuw_west
)
from signals.apps.signals.models import Signal, Status
from signals.celery import app


@app.task
def send_mail_reporter_created(pk):
    signal = Signal.objects.get(pk=pk)
    core.send_mail_reporter_created(signal)


@app.task
def send_mail_reporter_status_changed_split(signal_pk, status_pk):
    signal = Signal.objects.get(pk=signal_pk)
    status = Status.objects.get(pk=status_pk)
    core.send_mail_reporter_status_changed_split(signal, status)


@app.task
def send_mail_reporter_status_changed(signal_pk, status_pk):
    signal = Signal.objects.get(pk=signal_pk)
    status = Status.objects.get(pk=status_pk)
    core.send_mail_reporter_status_changed_afgehandeld(signal, status)
    core.send_mail_reporter_status_changed_in_behandeling(signal, status)


@app.task
def send_mail_apptimize(pk):
    signal = Signal.objects.get(pk=pk)
    apptimize.send_mail(signal)


@app.task
def send_mail_flex_horeca(pk):
    signal = Signal.objects.get(pk=pk)
    flex_horeca.send_mail(signal)


@app.task
def send_mail_handhaving_or_oost(pk):
    signal = Signal.objects.get(pk=pk)
    handhaving_or_oost.send_mail(signal)


@app.task
def send_mail_toezicht_or_nieuw_west(pk):
    signal = Signal.objects.get(pk=pk)
    toezicht_or_nieuw_west.send_mail(signal)


@app.task
def send_mail_vth_nieuw_west(pk):
    signal = Signal.objects.get(pk=pk)
    vth_nieuw_west.send_mail(signal)
