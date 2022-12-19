# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import copy
import json
import os
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

from signals.apps.gisib.data_loaders.quercus_tree_loader import QuercusTreeLoader
from signals.apps.gisib.models import GISIBFeature


@patch('signals.apps.gisib.protocol.requests.GISIBCollectionDeletedItemsRequest.get', autospec=True)
@patch('signals.apps.gisib.protocol.requests.GISIBCollectionWithFilterRequest.post', autospec=True)
class TestQuercusTreeLoader(TestCase):
    def setUp(self):
        self.feature_flags = copy.deepcopy(settings.FEATURE_FLAGS)
        self.feature_flags['GISIB_ENABLED'] = True

        filename = os.path.join(os.path.dirname(__file__),
                                '../mock_data/Collections_Boom_WithFilter_items_response.json')
        with open(filename) as f:
            self.mock_response_json = json.load(f)

        filename = os.path.join(os.path.dirname(__file__),
                                '../mock_data/empty_Collections_Boom_WithFilter_items_response.json')
        with open(filename) as f:
            self.mock_empty_response_json = json.load(f)

        filename = os.path.join(os.path.dirname(__file__),
                                '../mock_data/Collections_Boom_DeletedItems_response.json')
        with open(filename) as f:
            self.mock_deleted_items_response_json = json.load(f)

        filename = os.path.join(os.path.dirname(__file__),
                                '../mock_data/empty_Collections_Boom_DeletedItems_response.json')
        with open(filename) as f:
            self.mock_empty_deleted_items_response_json = json.load(f)

    def test_load_features(self, patched_collection_with_filter_request, patched_deleted_items_request):
        patched_collection_with_filter_request.return_value = self.mock_response_json
        patched_deleted_items_request.return_value = self.mock_deleted_items_response_json

        self.assertEqual(0, GISIBFeature.objects.count())

        time_delta = timedelta(days=2)
        with self.settings(FEATURE_FLAGS=self.feature_flags):
            loader = QuercusTreeLoader()
            loader._bearer_token = 'TestBearerToken'
            loader.load(time_delta=time_delta)

        self.assertEqual(9, GISIBFeature.objects.count())

    def test_load_no_features(self, patched_collection_with_filter_request, patched_deleted_items_request):
        patched_collection_with_filter_request.return_value = self.mock_empty_response_json
        patched_deleted_items_request.return_value = self.mock_empty_deleted_items_response_json

        self.assertEqual(0, GISIBFeature.objects.count())

        time_delta = timedelta(days=2)
        with self.settings(FEATURE_FLAGS=self.feature_flags):
            loader = QuercusTreeLoader()
            loader._bearer_token = 'TestBearerToken'
            loader.load(time_delta=time_delta)

        self.assertEqual(0, GISIBFeature.objects.count())
