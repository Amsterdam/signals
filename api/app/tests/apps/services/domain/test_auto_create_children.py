# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import copy
import json
import os
from unittest import mock

from django.test import TestCase, override_settings

from signals.apps.services.domain.auto_create_children import AutoCreateChildrenService
from signals.apps.signals.factories import SignalFactory, SignalFactoryWithImage
from signals.apps.signals.models import Category

THIS_DIR = os.path.dirname(__file__)


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
        self.category_overig = Category.objects.get(slug='overig', parent__isnull=False)
        self.extra_properties = [{
            'id': 'extra_container',
            'label': 'Container(s)',
            'answer': [
                {'id': 'ID001', 'type': 'Rest', 'description': 'Restafval container'},
                {'id': 'ID002', 'type': 'Plastic', 'description': 'Plasticafval container'},
                {'id': 'ID003', 'type': 'Papier', 'description': 'Papierafval container'},
                {'id': 'ID0004', 'type': 'Unknown', 'description': 'Unknown container'},
            ],
            'category_url': '/signals/v1/public/terms/categories/afval/sub_categories/container-is-vol'
        }, {
            'just': 'some',
            'additional': 'data',
            'that': 'should',
            'not': 'break',
            'the': 'test',
        }, ]

        filename = os.path.join(THIS_DIR, 'json', 'huidhoudelijkafval.json')
        with open(filename) as f:
            self.huishoudelijkafval_response = json.load(f)

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

    @mock.patch(
        'signals.apps.services.domain.auto_create_children.AutoCreateChildrenService._get_container_location',
        autospec=True
    )
    def test_multiple_extra_properties_for_containers(self, mocked):
        extra_properties = copy.deepcopy(self.extra_properties)
        extra_properties.append({
            'id': 'extra_container',
            'label': 'Container(s)',
            'answer': [
                {'id': 'ID011', 'type': 'Rest', 'description': 'Restafval container'},
                {'id': 'ID012', 'type': 'Plastic', 'description': 'Plasticafval container'},
                {'id': 'ID013', 'type': 'Papier', 'description': 'Papierafval container'},
                {'id': 'ID0014', 'type': 'Unknown', 'description': 'Unknown container'},
            ],
            'category_url': '/signals/v1/public/terms/categories/afval/sub_categories/container-is-vol'
        })

        signal = SignalFactory.create(extra_properties=extra_properties,
                                      category_assignment__category=self.category_container_is_vol)

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

        mocked.return_value = signal.location.geometrie

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertTrue(signal.is_parent)
        self.assertEqual(signal.children.count(), 8)

    @mock.patch(
        'signals.apps.services.domain.auto_create_children.AutoCreateChildrenService._get_container_location',
        autospec=True
    )
    def test_duplicate_extra_properties_for_containers(self, mocked):
        extra_properties = copy.deepcopy(self.extra_properties)
        extra_properties.append(self.extra_properties[0])

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
        extra_properties[0]['answer'] = [
            {'id': 'TEST-1', 'type': 'Rest', 'description': 'Restafval container'}
        ]

        signal = SignalFactory.create(extra_properties=extra_properties,
                                      category_assignment__category=self.category_container_is_vol)

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

    def test_too_many_containers_selected(self):
        extra_properties = copy.deepcopy(self.extra_properties)
        extra_properties[0]['answer'] = []

        for x in range(25):
            extra_properties[0]['answer'].append(
                {'id': f'TEST-{x}', 'type': 'Rest', 'description': 'Restafval container'}
            )

        signal = SignalFactory.create(extra_properties=extra_properties,
                                      category_assignment__category=self.category_container_is_vol)

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

    def test_wrong_category(self):
        extra_properties = copy.deepcopy(self.extra_properties)
        extra_properties[0]['category_url'] = self.category_overig.get_absolute_url()

        signal = SignalFactory.create(extra_properties=extra_properties,
                                      category_assignment__category=self.category_overig)

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

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

    def test_signal_kapot_to_vol(self):
        """
        Check that complaints in one of the broken container categories get
        children in one of the full container categories.
        """
        extra_properties = copy.deepcopy(self.extra_properties)

        full_slugs = set(AutoCreateChildrenService._type_2_category_slug.values())
        broken_slugs = AutoCreateChildrenService._trigger_types - full_slugs

        for sub_slug in broken_slugs:
            cat = Category.objects.get(slug=sub_slug, parent__isnull=False)
            cat_url = cat.get_absolute_url()
            extra_properties[0]['category_url'] = cat_url
            signal = SignalFactory.create(extra_properties=extra_properties, category_assignment__category=cat)

            self.assertFalse(signal.is_parent)
            self.assertEqual(signal.children.count(), 0)

            AutoCreateChildrenService.run(signal_id=signal.pk)

            signal.refresh_from_db()

            self.assertTrue(signal.is_parent)
            self.assertEqual(signal.children.count(), 4)

            for child in signal.children.all():
                self.assertIn(child.category_assignment.category.slug, full_slugs)

    @mock.patch(
        'signals.apps.services.domain.auto_create_children.AutoCreateChildrenService._get_container_location',
        autospec=True
    )
    def test_create_children_and_copy_attachments(self, mocked):
        extra_properties = copy.deepcopy(self.extra_properties)
        signal = SignalFactoryWithImage.create(extra_properties=extra_properties,
                                               category_assignment__category=self.category_container_is_vol)

        attachment_count = signal.attachments.filter(is_image=True).count()

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)
        self.assertEqual(attachment_count, 1)

        mocked.return_value = signal.location.geometrie

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertTrue(signal.is_parent)
        self.assertEqual(signal.children.count(), 4)

        for child in signal.children.all():
            self.assertEqual(child.attachments.filter(is_image=True).count(), attachment_count)
