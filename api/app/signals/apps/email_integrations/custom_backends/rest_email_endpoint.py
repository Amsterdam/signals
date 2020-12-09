import json
import threading

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from djcelery_email.utils import email_to_dict
from requests import RequestException, Session


class RestEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super(RestEmailBackend, self).__init__(fail_silently)
        self.init_kwargs = kwargs
        self.session = None
        self._lock = threading.RLock()
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
                verify=False
            )
            response.raise_for_status()
        except RequestException as e:
            if not self.fail_silently:
                raise e
            else:
                return False
        return True

    def open(self):
        if self.session:
            return False

        self.session = Session()
        self.session.cert = self.cert
        return True

    def close(self):
        if self.session is None:
            return
        self.session.close()
        self.session = None

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        with self._lock:
            session_created = self.open()
            if not self.session or session_created is None:
                # We failed silently on open().
                # Trying to send would be pointless.
                return 0
            num_sent = 0
            for message in email_messages:
                if self._send_email_rest_api(email_to_dict(message)):
                    num_sent += 1
            if session_created:
                self.close()
        return num_sent
