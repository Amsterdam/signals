# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import json
from unittest import mock

from django.core.mail import EmailMessage
from django.core.mail import send_mail as django_send_mail
from django.test import TestCase
from requests import Session

from signals.apps.email_integrations.custom_backends.rest_email_endpoint import RestEmailBackend


class TestRestEmailBackend(TestCase):
    def setUp(self):
        self.email = EmailMessage(
            'Hello',
            'Body goes here',
            'from@example.com',
            ['to1@example.com', 'Example <to2@example.com>'],
            ['bcc1@example.com', 'Example <bcc2@example.com>'],
            reply_to=['another@example.com'],
            headers={'Message-ID': 'foo'},
        )

    @mock.patch('signals.apps.email_integrations.custom_backends.rest_email_endpoint.RestEmailBackend._send_email_rest_api') # noqa
    def test_rest_email_backend_send_single_message(self, mocked_send):
        messages_sent = 0
        with self.settings(CELERY_EMAIL_MESSAGE_EXTRA_ATTRIBUTES=None):
            with RestEmailBackend() as backend:
                messages_sent += backend.send_messages([self.email])
        self.assertEqual(messages_sent, 1)
        mocked_send.assert_called_once()

    @mock.patch.object(Session, 'post')
    def test_rest_email_backend_post_request(self, mocked_session_post):
        with self.settings(CELERY_EMAIL_MESSAGE_EXTRA_ATTRIBUTES=None):
            with RestEmailBackend() as backend:
                backend.send_messages([self.email])

        expected_data = {
            'subject': 'Hello',
            'body': 'Body goes here',
            'from_email': 'from@example.com',
            'to': ['to1@example.com', 'to2@example.com'],
            'bcc': ['bcc1@example.com', 'bcc2@example.com'],
            'attachments': [],
            'headers': {
                'Message-ID': 'foo'
            },
            'cc': [],
            'reply_to': ['another@example.com']
        }

        mocked_session_post.assert_called_once_with(
            url=None,
            headers={'Content-type': 'application/json', 'Accept': 'text/plain'},
            data=json.dumps(expected_data),
            timeout=5
        )

    @mock.patch('signals.apps.email_integrations.custom_backends.rest_email_endpoint.RestEmailBackend._send_email_rest_api') # noqa
    def test_rest_email_backend_send_multiple_message(self, mocked_send):
        messages_sent = 0
        with self.settings(CELERY_EMAIL_MESSAGE_EXTRA_ATTRIBUTES=None):
            with RestEmailBackend() as backend:
                messages_sent += backend.send_messages([self.email, self.email])
        self.assertEqual(messages_sent, 2)
        self.assertEqual(mocked_send.call_count, 2)

    @mock.patch('signals.apps.email_integrations.custom_backends.rest_email_endpoint.RestEmailBackend._send_email_rest_api') # noqa
    def test_rest_email_backend_celery_config(self, mocked_send):
        with self.settings(
            CELERY_EMAIL_MESSAGE_EXTRA_ATTRIBUTES=None,
            EMAIL_BACKEND='djcelery_email.backends.CeleryEmailBackend',
            CELERY_EMAIL_BACKEND='signals.apps.email_integrations.custom_backends.rest_email_endpoint.RestEmailBackend'): # noqa

            django_send_mail(subject='test', message='Hello!', from_email='test@example.com',
                             recipient_list=['recipient@example.com'])
        mocked_send.assert_called_once()
