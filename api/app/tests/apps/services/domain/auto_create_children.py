# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import copy
from unittest import mock

from django.test import TestCase, override_settings

from signals.apps.services.domain.auto_create_children import AutoCreateChildrenService
from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models import Category


@override_settings(FEATURE_FLAGS={
    'API_SEARCH_ENABLED': False,
    'SEARCH_BUILD_INDEX': False,
    'API_DETERMINE_STADSDEEL_ENABLED': False,
    'API_FILTER_EXTRA_PROPERTIES': False,
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER': False,
    'API_TRANSFORM_SOURCE_IF_A_SIGNAL_IS_A_CHILD': False,
    'TASK_UPDATE_CHILDREN_BASED_ON_PARENT': False,
    'AUTOMATICALLY_CREATE_CHILD_SIGNALS_PER_CONTAINER': True,  # Interested in this functionality
})
class TestAutoCreateChildrenServiceService(TestCase):
    def setUp(self):
        self.category_container_is_vol = Category.objects.get(slug='container-is-vol', parent__isnull=False)
        self.extra_properties = [{
            "id": "extra_container",
            "label": "Container(s)",
            "answer": [
                {"id": "ID001", "type": "Rest", "description": "Restafval container"},
                {"id": "ID002", "type": "Plastic", "description": "Plasticafval container"},
                {"id": "ID003", "type": "Papier", "description": "Papierafval container"},
                {"id": "ID0004", "type": "Unknown", "description": "Unknown container"},
            ],
            "category_url": "/signals/v1/public/terms/categories/afval/sub_categories/container-is-vol"
        }]

    @mock.patch(
        'signals.apps.services.domain.auto_create_children.AutoCreateChildrenService._get_container_location',
        autospec=True
    )
    def test_create_children(self, mocked):
        extra_properties = copy.deepcopy(self.extra_properties)
        signal = SignalFactory.create(extra_properties=extra_properties,
                                      category_assignment__category=self.category_container_is_vol)

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

        mocked.return_value = signal.location.geometrie

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertTrue(signal.is_parent)
        self.assertEqual(signal.children.count(), 4)

    def test_no_containers_selected(self):
        signal = SignalFactory.create(extra_properties=None,
                                      category_assignment__category=self.category_container_is_vol)

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

    def test_one_container_selected(self):
        extra_properties = copy.deepcopy(self.extra_properties)
        extra_properties[0]['answer'] = [extra_properties[0]['answer'][0]]

        signal = SignalFactory.create(extra_properties=None,
                                      category_assignment__category=self.category_container_is_vol)

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

    @mock.patch(
        'signals.apps.services.domain.auto_create_children.AutoCreateChildrenService._get_container_location',
        autospec=True
    )
    def test_multiple_extra_properties_for_containers(self, mocked):
        extra_properties = copy.deepcopy(self.extra_properties)
        extra_properties.append(copy.deepcopy(extra_properties[0]))

        signal = SignalFactory.create(extra_properties=extra_properties,
                                      category_assignment__category=self.category_container_is_vol)

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

        mocked.return_value = signal.location.geometrie

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertTrue(signal.is_parent)
        self.assertEqual(signal.children.count(), 8)

    def test_signal_wrong_state(self):
        extra_properties = copy.deepcopy(self.extra_properties)
        signal = SignalFactory.create(extra_properties=extra_properties,
                                      category_assignment__category=self.category_container_is_vol,
                                      status__state='i')

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

    @override_settings(FEATURE_FLAGS={
        'AUTOMATICALLY_CREATE_CHILD_SIGNALS_PER_CONTAINER': False,  # Interested in this functionality
    })
    def test_signal_feature_disabled(self):
        extra_properties = copy.deepcopy(self.extra_properties)
        signal = SignalFactory.create(extra_properties=extra_properties,
                                      category_assignment__category=self.category_container_is_vol)

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)
