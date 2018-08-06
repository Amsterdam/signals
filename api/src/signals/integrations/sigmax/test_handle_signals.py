import os
import json
import datetime
import copy
from unittest import mock
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from django.test.utils import override_settings
from jsonschema.exceptions import ValidationError
import pytz
import requests

from datasets import handle_signals
from datasets.models import MessageLog
from datasets.external.base import reset_handlers


# -- test _get_session_with_retries --

class TestGetSessionWithRetries(TestCase):
    def test_returns_session_instance(self):
        test_session = handle_signals._get_session_with_retries()
        self.assertIsInstance(test_session, requests.Session)


# -- _call_external_apis --

SIGNAL_PLACEHOLDERS = [
    {
        "signal_id": "1"
    },
    {
        "signal_id": "2"
    },
    {
        "signal_id": "4"
    }
]


class TestCallExternalApis(TestCase):
    def setUp(self):
        reset_handlers()
        MessageLog.objects.create(
            signal_id='1',
            t_entered=timezone.now(),
            t_sent=timezone.now(),
            handler_name='some-handler',
            status='200',
            is_sent=True
        )

    def test_signals_handled_only_once(self):
        signals = SIGNAL_PLACEHOLDERS

        # check that the sigals are only added to the database once
        handle_signals._call_external_apis(signals)
        self.assertEquals(MessageLog.objects.count(), 3)

        handle_signals._call_external_apis(signals)
        self.assertEquals(MessageLog.objects.count(), 3)

    def test_signal_handlers(self):
        self.assertEquals(MessageLog.objects.count(), 1)
        signals = SIGNAL_PLACEHOLDERS

        # check that the signals are handled by the correct handlers
        handle_signals._call_external_apis(signals)
        self.assertEquals(
            MessageLog.objects.filter(handler_name='local-log-only').count(), 2)
        # Note: this test assumes that the LogOnlyHandler fallback is present.


# -- test _validate_signal_api_data --

class TestValidateSignalApi(TestCase):
    @classmethod
    def setUpClass(cls):
        fixture_file = os.path.join(
            settings.FIXTURES_DIR, 'datasets', 'internal', 'auth_signal.json')

        with open(fixture_file, 'r') as f:
            test_data = json.load(f)
        cls._example_signal = test_data['results'][0]

    @classmethod
    def tearDownClass(cls):
        pass

    def test_signal(self):
        signal = copy.deepcopy(self._example_signal)
        handle_signals._validate_signal_api_data(signal)

    def test_fails_on_bad_data(self):
        signal = '{ This is not JSON at all!'
        with self.assertRaises(ValidationError):
            handle_signals._validate_signal_api_data(signal)


# -- test _batch_signals --

_NO_PAGINATION = {
    'results': [
        {'signal_id': '1'},
        {'signal_id': '2'}
    ]
}

_TWO_PAGES = [{
    '_links': {
        'next': {
            'href': 'WHATEVER'
        },
    },
    'results': [
        {'signal_id': '1'},
        {'signal_id': '2'}
    ]
},
{
    '_links': {
        'next': {
            'href': None
        },
    },
    'results': [
        {'signal_id': '3'},
        {'signal_id': '4'}
    ]
}]


class TestBatchSignals(TestCase):
    @patch('requests.Session.get')
    def test_no_pagination_links(self, patched_get):
        with self.assertRaises(KeyError):
            patched_json = mock.MagicMock()
            patched_json.json = mock.MagicMock()
            patched_json.json.return_value = _NO_PAGINATION

            patched_get.return_value = patched_json
            for page in handle_signals._batch_signals('NO MATTER'):
                pass

        self.assertTrue(patched_json.json.called)

    @patch('requests.Session.get')
    def test_two_pages(self, patched_get):
        patched_json = mock.MagicMock()
        patched_json.json = mock.MagicMock()
        patched_json.json.return_value = _TWO_PAGES[0]

        patched_get.return_value = patched_json
        for page in handle_signals._batch_signals('NO MATTER'):
            patched_json.json.return_value = _TWO_PAGES[1]  # simulate the second page

        self.assertEquals(patched_get.call_count, 2)
        self.assertEquals(patched_json.json.call_count, 2)


# -- test handle_signals --

class TestHandleSignals(TestCase):
    def setUp(self):
        reset_handlers()

    @patch('datasets.handle_signals._batch_signals')
    @patch('datasets.internal.get_auth_token.GetAccessToken.getAccessToken')
    def test_handle_signals(self, patched_get_access_token, patched_batch):
        patched_get_access_token.return_value = {'Authorization', 'DOES NOT MATTER'}
        patched_batch.return_value = [[{'signal_id': 1}, {'signal_id': 2}], [{'signal_id': 3}]]

        handle_signals.handle_signals()

        self.assertEquals(patched_get_access_token.call_count, 1)
        self.assertEquals(patched_batch.call_count, 1)

        self.assertEquals(
            MessageLog.objects.filter(handler_name='local-log-only').count(), 3)
