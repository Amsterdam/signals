# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from signals.apps.signals.factories import StoredSignalFilterFactory
from signals.apps.signals.models import StoredSignalFilter
from signals.test.utils import SIAReadUserMixin, SignalsBaseApiTestCase


class TestStoredSignalFilters(SIAReadUserMixin, SignalsBaseApiTestCase):
    test_host = 'http://testserver'
    endpoint = '/signals/v1/private/me/filters/'

    def setUp(self):
        # Forcing authentication
        self.client.force_authenticate(user=self.sia_read_user)

    def test_no_filters(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(200, response.status_code)

        data = response.json()
        self.assertEqual(0, data['count'])
        self.assertEqual(0, len(data['results']))

    def test_no_filters_for_current_user(self):
        StoredSignalFilterFactory.create_batch(5, created_by=self.user)
        self.assertEqual(5, StoredSignalFilter.objects.count())

        response = self.client.get(self.endpoint)
        self.assertEqual(200, response.status_code)

        data = response.json()
        self.assertEqual(0, data['count'])
        self.assertEqual(0, len(data['results']))

    def test_filters_for_current_user(self):
        StoredSignalFilterFactory.create_batch(5, created_by=self.sia_read_user)
        self.assertEqual(5, StoredSignalFilter.objects.count())

        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(5, data['count'])
        self.assertEqual(5, len(data['results']))

    def test_create_filter(self):
        data = {
            'name': 'Created my first filter',
            'options': {
                'status': [
                    'i',
                ]
            },
        }

        response = self.client.post(self.endpoint, data, format='json')
        self.assertEqual(201, response.status_code)

        response_data = response.json()
        self.assertEqual('Created my first filter', response_data['name'])
        self.assertIn('options', response_data)
        self.assertIn('status', response_data['options'])
        self.assertEqual(1, len(response_data['options']['status']))
        self.assertIn('i', response_data['options']['status'])
        self.assertFalse(response_data['refresh'])
        self.assertFalse(response_data['show_on_overview'])

    def test_create_filter_missing_options_no_500(self):
        data = {
            'name': 'MISSING OPTIONS SHOULD ALSO WORK'
        }

        response = self.client.post(self.endpoint, data, format='json')
        self.assertEqual(400, response.status_code)

        response_data = response.json()
        self.assertEqual(
            response_data['non_field_errors'][0], 'No filters specified, "options" object missing.')

    def test_update_filter(self):
        sia_read_user_filter = StoredSignalFilterFactory.create(
            created_by=self.sia_read_user
        )
        uri = '{}{}'.format(self.endpoint, sia_read_user_filter.id)

        response = self.client.get(uri)
        self.assertEqual(200, response.status_code)
        response_data = response.json()
        self.assertIn('options', response_data)
        self.assertNotIn('status', response_data['options'])

        data = {'options': {
            'status': [
                'i',
            ]
        }}

        response = self.client.patch(uri, data, format='json')
        self.assertEqual(200, response.status_code)

        response_data = response.json()
        self.assertIn('options', response_data)
        self.assertIn('status', response_data['options'])
        self.assertEqual(1, len(response_data['options']['status']))
        self.assertIn('i', response_data['options']['status'])
        self.assertEqual(sia_read_user_filter.refresh, response_data['refresh'])
        self.assertFalse(response_data['show_on_overview'])

    def test_delete_filter(self):
        sia_read_user_filter = StoredSignalFilterFactory.create(
            created_by=self.sia_read_user
        )

        uri = '{}{}'.format(self.endpoint, sia_read_user_filter.id)
        response = self.client.delete(uri)
        self.assertEqual(204, response.status_code)

    def test_get_not_my_filter(self):
        user_filter = StoredSignalFilterFactory.create(created_by=self.user)

        uri = '{}{}'.format(self.endpoint, user_filter.id)
        response = self.client.get(uri)
        self.assertEqual(404, response.status_code)

    def test_update_not_my_filter(self):
        user_filter = StoredSignalFilterFactory.create(created_by=self.user)

        uri = '{}{}'.format(self.endpoint, user_filter.id)
        response = self.client.put(uri, data={'name': 'this_is_not_allowed_for_the_current_user'})
        self.assertEqual(404, response.status_code)

    def test_delete_not_my_filter(self):
        user_filter = StoredSignalFilterFactory.create(created_by=self.user)

        uri = '{}{}'.format(self.endpoint, user_filter.id)
        response = self.client.delete(uri)
        self.assertEqual(404, response.status_code)

    def test_create_filter_refresh(self):
        data = {
            'name': 'Created my first filter',
            'options': {
                'status': [
                    'i',
                ]
            },
            'refresh': True,
        }

        response = self.client.post(self.endpoint, data, format='json')
        self.assertEqual(201, response.status_code)

        response_data = response.json()
        self.assertEqual('Created my first filter', response_data['name'])
        self.assertIn('options', response_data)
        self.assertIn('status', response_data['options'])
        self.assertEqual(1, len(response_data['options']['status']))
        self.assertIn('i', response_data['options']['status'])
        self.assertTrue(response_data['refresh'])
        self.assertFalse(response_data['show_on_overview'])

    def test_do_not_store_unknown_filters(self):
        filter_name = 'Dit mag niet opgeslagen worden.'
        data = {
            'name': filter_name,
            'options': {
                'nonsense': ['none', 'email'],
                'garbage': 'blah',
            }
        }

        response = self.client.post(self.endpoint, data, format='json')
        self.assertEqual(400, response.status_code)

        self.assertIn('nonsense', repr(response.json()['options']))
        self.assertIn('garbage', repr(response.json()['options']))

    def test_create_filter_bad_inputs_no_500(self):
        BAD_INPUTS = [
            ['ABC', 'DEF'],
            'ABCDEF',
            None,
            1234,
        ]

        for bad_input in BAD_INPUTS:
            data = {
                'name': 'Dit mag niet opgeslagen worden.',
                'options': bad_input
            }

            response = self.client.post(self.endpoint, data, format='json')
            self.assertEqual(400, response.status_code)

    def test_create_filter_show_on_overview(self):
        """
        SIG-3923 Added 'show_on_overview' flag
        """
        data = {
            'name': 'Created my first filter',
            'options': {
                'status': [
                    'i',
                ]
            },
            'show_on_overview': True
        }

        response = self.client.post(self.endpoint, data, format='json')
        self.assertEqual(201, response.status_code)

        response_data = response.json()
        self.assertEqual('Created my first filter', response_data['name'])
        self.assertIn('options', response_data)
        self.assertIn('status', response_data['options'])
        self.assertEqual(1, len(response_data['options']['status']))
        self.assertIn('i', response_data['options']['status'])
        self.assertFalse(response_data['refresh'])
        self.assertTrue(response_data['show_on_overview'])

    def test_update_filter_show_on_overview(self):
        """
        SIG-3923 Added 'show_on_overview' flag
        """
        sia_read_user_filter = StoredSignalFilterFactory.create(
            created_by=self.sia_read_user
        )
        uri = '{}{}'.format(self.endpoint, sia_read_user_filter.id)

        response = self.client.get(uri, format='json')
        self.assertEqual(200, response.status_code)

        response_data = response.json()
        self.assertFalse(response_data['show_on_overview'])

        data = {
            'show_on_overview': True
        }

        response = self.client.patch(uri, data, format='json')
        self.assertEqual(200, response.status_code)

        response_data = response.json()
        self.assertTrue(response_data['show_on_overview'])

        data = {
            'show_on_overview': False
        }

        response = self.client.patch(uri, data, format='json')
        self.assertEqual(200, response.status_code)

        response_data = response.json()
        self.assertFalse(response_data['show_on_overview'])
