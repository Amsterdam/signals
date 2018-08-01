from signals.celery import app


@app.task
def push_to_sigmax(id):
    pass


@app.task
def email_to_apptimize(id):
    pass
