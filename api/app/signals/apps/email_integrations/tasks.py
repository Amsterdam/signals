from signals.celery import app

from signals.apps.email_integrations import apptimize, default, flex_horeca


@app.task
def send_mail_reporter(signal):
    default.send_mail_reporter(signal)


@app.task
def send_mail_status_change(status, prev_status):
    default.send_mail_status_change(status, prev_status)


@app.task
def send_mail_apptimize(pk):
    apptimize.send_mail(pk)


@app.task
def send_mail_flex_horeca(pk):
    flex_horeca.send_mail(pk)

