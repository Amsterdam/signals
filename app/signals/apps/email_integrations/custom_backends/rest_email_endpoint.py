# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import base64
import json
import threading
from email.mime.base import MIMEBase
from email.utils import parseaddr

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail.backends.base import BaseEmailBackend
from requests import RequestException, Session


class RestEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently)
        self.init_kwargs = kwargs
        self.session = None
        self._lock = threading.RLock()

        self.cert = None
        if settings.EMAIL_REST_ENDPOINT_CLIENT_CERT and settings.EMAIL_REST_ENDPOINT_CLIENT_KEY:
            self.cert = (settings.EMAIL_REST_ENDPOINT_CLIENT_CERT, settings.EMAIL_REST_ENDPOINT_CLIENT_KEY)

        self.verify = True
        if settings.EMAIL_REST_ENDPOINT_CA_BUNDLE:
            self.verify = settings.EMAIL_REST_ENDPOINT_CA_BUNDLE

    def _send_email_rest_api(self, message_attributes):
        try:
            response = self.session.post(
                url=settings.EMAIL_REST_ENDPOINT,
                headers={'Content-type': 'application/json', 'Accept': 'text/plain'},
                data=json.dumps(message_attributes),
                timeout=settings.EMAIL_REST_ENDPOINT_TIMEOUT
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
        self.session.verify = self.verify
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
                if self._send_email_rest_api(self._email_to_dict(message)):
                    num_sent += 1
            if session_created:
                self.close()
        return num_sent

    def _email_to_dict(self, message):
        if isinstance(message, dict):
            return message

        message_dict = {
            'subject': message.subject,
            'body': message.body,
            'from_email': parseaddr(message.from_email)[1],
            'to': [parseaddr(addr)[1] for addr in message.to],
            'bcc': [parseaddr(addr)[1] for addr in message.bcc],
            # ignore connection
            'attachments': [],
            'headers': message.extra_headers,
            'cc': [parseaddr(addr)[1] for addr in message.cc],
            'reply_to': [parseaddr(addr)[1] for addr in message.reply_to]
        }

        if hasattr(message, 'alternatives'):
            message_dict['alternatives'] = message.alternatives
        if message.content_subtype != EmailMessage.content_subtype:
            message_dict["content_subtype"] = message.content_subtype
        if message.mixed_subtype != EmailMessage.mixed_subtype:
            message_dict["mixed_subtype"] = message.mixed_subtype

        attachments = message.attachments
        for attachment in attachments:
            if isinstance(attachment, MIMEBase):
                filename = attachment.get_filename('')
                binary_contents = attachment.get_payload(decode=True)
                mimetype = attachment.get_content_type()
            else:
                filename, binary_contents, mimetype = attachment
                # For a mimetype starting with text/, content is expected to be a string.
                if isinstance(binary_contents, str):
                    binary_contents = binary_contents.encode()
            contents = base64.b64encode(binary_contents).decode('ascii')
            message_dict['attachments'].append((filename, contents, mimetype))

        return message_dict
