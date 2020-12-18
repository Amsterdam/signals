from django.contrib.auth.models import Permission
from django.test import override_settings

from signals.apps.signals.factories import SignalFactoryValidLocation
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase


@override_settings(FEATURE_FLAGS={
    'API_SEARCH_ENABLED': False,
    'SEARCH_BUILD_INDEX': False,
    'API_DETERMINE_STADSDEEL_ENABLED': True,
    'API_FILTER_EXTRA_PROPERTIES': True,
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER': True,
    'API_TRANSFORM_SOURCE_IF_A_SIGNAL_IS_A_CHILD': False,
    'API_VALIDATE_SOURCE_AGAINST_SOURCE_MODEL': False,
    'TASK_UPDATE_CHILDREN_BASED_ON_PARENT': False,
})
class TestPrivateSignalViewSet(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    endpoint = '/signals/v1/private/signals/geography'

    def setUp(self):
        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))

    def test_geo_list_endpoint(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        SignalFactoryValidLocation.create_batch(2)

        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['features']), 2)

        # Check headers
        self.assertTrue(response.has_header('Link'))
        self.assertTrue(response.has_header('X-Total-Count'))
        self.assertEqual(response['X-Total-Count'], '2')

    def test_geo_list_endpoint_paginated(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        SignalFactoryValidLocation.create_batch(2)

        # the first page
        response = self.client.get(self.endpoint, data={'page_size': 1})
        self.assertEqual(response.status_code, 200)

        # Check headers
        self.assertTrue(response.has_header('Link'))
        links = response['Link'].split(',')
        self.assertEqual(len(links), 2)
        self.assertIn('rel="self"', links[0])
        self.assertIn('rel="next"', links[1])
        self.assertNotIn('rel="previous"', links[1])

        self.assertTrue(response.has_header('X-Total-Count'))
        self.assertEqual(response['X-Total-Count'], '2')

        self.assertEqual(len(response.json()['features']), 1)

        # the second page
        response = self.client.get(links[1].split(';')[0][1:-1])  # The next page

        self.assertTrue(response.has_header('Link'))
        links = response['Link'].split(',')
        self.assertEqual(len(links), 2)
        self.assertIn('rel="self"', links[0])
        self.assertNotIn('rel="next"', links[1])
        self.assertIn('rel="prev"', links[1])

        self.assertTrue(response.has_header('X-Total-Count'))
        self.assertEqual(response['X-Total-Count'], '2')

        self.assertEqual(len(response.json()['features']), 1)
