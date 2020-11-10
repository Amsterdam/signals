import json

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from djcelery_email.utils import chunked, email_to_dict
from requests import RequestException, Session


class RestEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super(RestEmailBackend, self).__init__(fail_silently)
        self.init_kwargs = kwargs

    def _send_email_rest_api(self, session, message):
        try:
            response = session.post(
                url=settings.EMAIL_REST_ENDPOINT,
                data=json.dumps(message),
                timeout=settings.EMAIL_REST_ENDPOINT_TIMEOUT,
            )
            response.raise_for_status()
        except RequestException as e:
            if not self.fail_silently:
                raise e
            else:
                return False
        return True

    def send_messages(self, email_messages):
        messages_sent = 0
        s = Session()
        # init session, connection using client and server side certificate is expensive
        if hasattr(settings, 'EMAIL_REST_ENDPOINT_CLIENT_CERT') and hasattr(settings, 'EMAIL_REST_ENDPOINT_CLIENT_KEY'): # noqa
            s.cert = (settings.EMAIL_REST_ENDPOINT_CLIENT_CERT, settings.EMAIL_REST_ENDPOINT_CLIENT_KEY)

        for chunk in chunked(email_messages, settings.CELERY_EMAIL_CHUNK_SIZE):
            chunk_messages = [email_to_dict(msg) for msg in chunk]
            if self._send_email_rest_api(s, chunk_messages):
                messages_sent += 1
        return messages_sent
