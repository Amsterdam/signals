from signals.apps.email_integrations.mail_actions import MailActions
from signals.apps.email_integrations.reporter_rules import SIGNAL_MAIL_RULES
from signals.celery import app


@app.task
def send_mail_reporter(pk):
    MailActions(mail_rules=SIGNAL_MAIL_RULES).apply(signal_id=pk)
