"""
Test and document the behavior of the Signal instance updates via patches.
"""
import os
import unittest
from unittest import mock
from urllib.parse import urlparse

from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError

from signals.apps.signals import workflow
from signals.apps.signals.managers import (
    create_note,
    update_category_assignment,
    update_location,
    update_priority,
    update_status,
    update_type
)
from signals.apps.signals.models import Category
from tests.apps.signals import factories
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)


class TestAtomicityOfPatch(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    """
    PATCH update to Signal instances must be atomic.
    """

    def assertUrlPathMatch(self, url1, url2):
        path1 = urlparse(url1).path
        path2 = urlparse(url2).path

        self.assertEqual(path1, path2)

    def setUp(self):
        self.list_endpoint = '/signals/v1/private/signals/'
        self.detail_endpoint = '/signals/v1/private/signals/{pk}'
        self.history_endpoint = '/signals/v1/private/signals/{id}/history'

        self.signal = factories.SignalFactoryWithImage.create(
            status__state=workflow.GEMELD,
            status__text='INITIAL',
        )

        self.test_cat_main = factories.CategoryFactory.create(
            parent=None,
            name='CAT_MAIN',
            handling=Category.HANDLING_REST,
        )
        self.test_cat_sub = factories.CategoryFactory.create(
            parent=self.test_cat_main,
            name='CAT_SUB',
            handling=Category.HANDLING_REST,
        )

        self.link_test_cat_sub = '/signals/v1/public/terms/categories/{}/sub_categories/{}'.format(
            self.test_cat_sub.parent.slug, self.test_cat_sub.slug
        )

        # Payload for signal PATCH requests
        self.payload = {
            'status': {
                'state': workflow.BEHANDELING,
                'text': 'TEST STATUS UPDATE',
            },
            'category': {
                'sub_category': self.link_test_cat_sub,
                'text': 'TEST CATEGORY ASSIGNMENT UPDATE',
            },
            'notes': [{
                'text': 'TEST NOTE BODY',
            }],
            'types': [{
                'code': 'SIG',
            }]
        }

        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))

    def test_update_status_and_category(self):
        """
        Test happy flow PATCH update to status and category assignment.
        """
        self.client.force_authenticate(user=self.sia_read_write_user)
        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)

        response = self.client.patch(detail_endpoint, data=self.payload, format='json')
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        # Check that our double update worked
        self.assertEqual(response_data['status']['state'], self.payload['status']['state'])
        self.assertEqual(response_data['status']['text'], response_data['status']['text'])

        self.assertUrlPathMatch(
            response_data['category']['category_url'], self.payload['category']['sub_category'])
        self.assertEqual(response_data['category']['text'], self.payload['category']['text'])

    @mock.patch(
        'signals.apps.signals.managers.SignalManager._update_category_assignment_no_transaction',
        autospec=True
    )
    def test_update_status_and_failed_category(self, mocked):
        self.client.force_authenticate(user=self.sia_read_write_user)
        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)

        # Store status and category url before attempted PATCH
        response = self.client.get(detail_endpoint)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        status_before = response_data['status']['state']
        category_url_before = response_data['category']['category_url']

        # Update signal instance (use invalid category assignment data)
        mocked.side_effect = ValidationError('Something, something, error!')
        self.payload['category']['sub_category'] = self.link_test_cat_sub
        response = self.client.patch(detail_endpoint, data=self.payload, format='json')
        self.assertEqual(response.status_code, 400)

        # Check the state / category after this failed patch (desired behavior
        # is that the update fails in full).
        response = self.client.get(detail_endpoint)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        # We want no mutation to either category url or status.
        self.assertUrlPathMatch(response_data['category']['category_url'], category_url_before)
        self.assertEqual(response_data['status']['state'], status_before)

    @mock.patch('signals.apps.signals.managers.SignalManager._update_status_no_transaction',
                autospec=True)
    def test_update_category_and_failed_status(self, mocked):
        self.client.force_authenticate(user=self.sia_read_write_user)
        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)

        # Store status and category url before attempted PATCH
        response = self.client.get(detail_endpoint)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        status_before = response_data['status']['state']
        category_url_before = response_data['category']['category_url']

        # Update signal instance (use invalid status data)
        mocked.side_effect = ValidationError('Something, something, error!')
        self.payload['status']['state'] = workflow.BEHANDELING
        response = self.client.patch(detail_endpoint, data=self.payload, format='json')
        self.assertEqual(response.status_code, 400)

        # Check the state / category after this failed patch (desired behavior
        # is that the update fails in full).
        response = self.client.get(detail_endpoint)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        # We want no mutation to either category url or status.
        self.assertUrlPathMatch(response_data['category']['category_url'], category_url_before)
        self.assertEqual(response_data['status']['state'], status_before)

    @mock.patch('signals.apps.signals.managers.SignalManager._create_note_no_transaction',
                autospec=True)
    def test_partial_fail_no_django_signals_fired(self, mocked):
        # Receiver for Django signals involved in PATCHes to SIA Signal instances
        fake_receiver = unittest.mock.MagicMock()

        update_location.connect(fake_receiver)
        update_status.connect(fake_receiver)
        update_category_assignment.connect(fake_receiver)
        update_priority.connect(fake_receiver)
        create_note.connect(fake_receiver)
        update_type.connect(fake_receiver)

        # Perform a PATCH with in,valid category assignment:
        self.client.force_authenticate(user=self.sia_read_write_user)
        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)

        mocked.side_effect = ValidationError('Something, something, error!')
        self.payload['category']['sub_category'] = self.link_test_cat_sub
        response = self.client.patch(detail_endpoint, data=self.payload, format='json')
        self.assertEqual(response.status_code, 400)

        # Assert that our fake receiver was never called.
        fake_receiver.assert_not_called()
