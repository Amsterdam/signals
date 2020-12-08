import json

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from djcelery_email.utils import chunked, email_to_dict
from requests import RequestException, Session


class RestEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super(RestEmailBackend, self).__init__(fail_silently)
        self.init_kwargs = kwargs
        self.session = None
        self.cert = None
        if hasattr(settings, 'EMAIL_REST_ENDPOINT_CLIENT_CERT') and hasattr(settings, 'EMAIL_REST_ENDPOINT_CLIENT_KEY'): # noqa
            self.cert = (settings.EMAIL_REST_ENDPOINT_CLIENT_CERT, settings.EMAIL_REST_ENDPOINT_CLIENT_KEY)

    def _send_email_rest_api(self, message_attributes):
        try:
            response = self.session.post(
                url=settings.EMAIL_REST_ENDPOINT,
                headers={'Content-type': 'application/json', 'Accept': 'text/plain'},
                data=json.dumps(message_attributes),
                timeout=settings.EMAIL_REST_ENDPOINT_TIMEOUT,
            )
            response.raise_for_status()
        except RequestException as e:
            if not self.fail_silently:
                raise e
            else:
                return False
        return True

    def open(self):
        self.session = Session()
        self.session.cert = self.cert

    def close(self):
        self.session.close()
        self.session = None

    def send_messages(self, email_messages):
        messages_sent = 0

        for chunk in chunked(email_messages, settings.CELERY_EMAIL_CHUNK_SIZE):
            message_attributes = [email_to_dict(msg) for msg in chunk]
            if self._send_email_rest_api(message_attributes):
                messages_sent += 1
        return messages_sent
