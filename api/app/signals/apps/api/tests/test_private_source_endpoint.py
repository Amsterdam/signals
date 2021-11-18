# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import os

from rest_framework import status

from signals.apps.signals.factories import SourceFactory
from signals.apps.signals.models import Source
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)


class TestPrivateSourceEndpointUnAuthorized(SignalsBaseApiTestCase):
    def test_list_endpoint(self):
        response = self.client.get('/signals/v1/private/signals/')
        self.assertEqual(response.status_code, 401)


class TestPrivateSourceEndpoint(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    list_endpoint = '/signals/v1/private/sources/'

    def setUp(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        self.list_sources_schema = self.load_json_schema(
            os.path.join(THIS_DIR, 'json_schema', 'get_signals_v1_private_sources.json')
        )

    def test_get_list(self):
        SourceFactory.create_batch(5)
        self.assertEqual(Source.objects.count(), 5)

        response = self.client.get(f'{self.list_endpoint}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(5, data['count'])
        self.assertEqual(5, len(data['results']))
        self.assertJsonSchema(self.list_sources_schema, data)

    def test_get_list_is_active_filter(self):
        # setup
        active_sources = SourceFactory.create_batch(3)
        inactive_sources = SourceFactory.create_batch(2, is_active=False)
        self.assertEqual(Source.objects.count(), 5)
        self.assertEqual(Source.objects.filter(is_active=True).count(), 3)
        self.assertEqual(Source.objects.filter(is_active=False).count(), 2)

        # is_active = true
        response = self.client.get(f'{self.list_endpoint}?is_active=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertJsonSchema(self.list_sources_schema, data)

        self.assertEqual(3, data['count'])
        self.assertEqual(3, len(data['results']))

        active_source_ids = [active_source.id for active_source in active_sources]
        result_ids = [result['id'] for result in data['results']]

        self.assertEqual(set(active_source_ids), set(result_ids))

        # is_active = false
        response = self.client.get(f'{self.list_endpoint}?is_active=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertJsonSchema(self.list_sources_schema, data)

        self.assertEqual(2, data['count'])
        self.assertEqual(2, len(data['results']))

        inactive_source_ids = [inactive_source.id for inactive_source in inactive_sources]
        result_ids = [result['id'] for result in data['results']]

        self.assertEqual(set(inactive_source_ids), set(result_ids))

    def test_get_list_can_be_selected_filter(self):
        # setup
        can_be_selected_sources = SourceFactory.create_batch(3, can_be_selected=True, is_active=True)
        can_not_be_selected_sources = SourceFactory.create_batch(2, can_be_selected=False, is_active=True)

        self.assertEqual(Source.objects.count(), 5)
        self.assertEqual(Source.objects.filter(can_be_selected=True).count(), 3)
        self.assertEqual(Source.objects.filter(can_be_selected=False).count(), 2)

        # can_be_selected = true
        response = self.client.get(f'{self.list_endpoint}?can_be_selected=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertJsonSchema(self.list_sources_schema, data)

        self.assertEqual(3, data['count'])
        self.assertEqual(3, len(data['results']))

        source_ids = [source.id for source in can_be_selected_sources]
        result_ids = [result['id'] for result in data['results']]

        self.assertEqual(set(source_ids), set(result_ids))

        # can_be_selected = false
        response = self.client.get(f'{self.list_endpoint}?can_be_selected=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertJsonSchema(self.list_sources_schema, data)

        self.assertEqual(2, data['count'])
        self.assertEqual(2, len(data['results']))

        source_ids = [source.id for source in can_not_be_selected_sources]
        result_ids = [result['id'] for result in data['results']]

        self.assertEqual(set(source_ids), set(result_ids))

    def test_post_method_not_allowed(self):
        response = self.client.post(f'{self.list_endpoint}1', data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_patch_method_not_allowed(self):
        response = self.client.patch(f'{self.list_endpoint}1', data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_method_not_allowed(self):
        response = self.client.delete(f'{self.list_endpoint}1')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
