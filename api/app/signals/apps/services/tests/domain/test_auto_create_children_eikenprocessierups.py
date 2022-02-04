# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import copy
import os

from django.test import TestCase, override_settings

from signals.apps.services.domain.auto_create_children.service import AutoCreateChildrenService
from signals.apps.signals.factories import SignalFactory, SignalFactoryWithImage
from signals.apps.signals.models import Category

THIS_DIR = os.path.dirname(__file__)


@override_settings(FEATURE_FLAGS={
    'API_DETERMINE_STADSDEEL_ENABLED': False,
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER': False,
    'TASK_UPDATE_CHILDREN_BASED_ON_PARENT': False,
    'AUTOMATICALLY_CREATE_CHILD_SIGNALS_PER_CONTAINER': False,
    'AUTOMATICALLY_CREATE_CHILD_SIGNALS_PER_EIKENPROCESSIERUPS_TREE': True,  # Interested in this functionality
})
class TestAutoCreateChildrenServiceService(TestCase):
    def setUp(self):
        self.category_eikenprocessierups = Category.objects.get(slug='eikenprocessierups', parent__isnull=False)
        self.category_overig = Category.objects.get(slug='overig', parent__isnull=False)
        self.extra_properties = [{
            'id': 'extra_eikenprocessierups',
            'label': 'Boom',
            'answer': [
                {'id': 'ID001', 'type': 'Eikenboom', 'GlobalID': '00000000-0000-0000-0000-000000000000',
                 'isReported': False, 'description': 'Eikenboom'},
                {'id': 'ID002', 'type': 'Eikenboom', 'GlobalID': '00000000-0000-0000-0000-000000000000',
                 'isReported': False, 'description': 'Eikenboom'},
                {'id': 'ID003', 'type': 'Eikenboom', 'GlobalID': '00000000-0000-0000-0000-000000000000',
                 'isReported': False, 'description': 'Eikenboom'},
                {'id': 'ID004', 'type': 'Eikenboom', 'GlobalID': '00000000-0000-0000-0000-000000000000',
                 'isReported': False, 'description': 'Eikenboom'},
            ],
            'category_url': '/signals/v1/public/terms/categories/openbaar-groen-en-water/sub_categories/eikenprocessierups'  # noqa
        }, {
            'just': 'some',
            'additional': 'data',
            'that': 'should',
            'not': 'break',
            'the': 'test',
        }, ]

    def test_create_children(self):
        extra_properties = copy.deepcopy(self.extra_properties)
        signal = SignalFactory.create(extra_properties=extra_properties,
                                      category_assignment__category=self.category_eikenprocessierups)

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertTrue(signal.is_parent)
        self.assertEqual(signal.children.count(), 4)

    def test_multiple_extra_properties_for_trees(self):
        extra_properties = copy.deepcopy(self.extra_properties)
        extra_properties.append({
            'id': 'extra_eikenprocessierups',
            'label': 'Boom',
            'answer': [
                {'id': 'ID011', 'type': 'Eikenboom', 'GlobalID': '00000000-0000-0000-0000-000000000000',
                 'isReported': False, 'description': 'Eikenboom'},  # noqa
                {'id': 'ID012', 'type': 'Eikenboom', 'GlobalID': '00000000-0000-0000-0000-000000000000',
                 'isReported': False, 'description': 'Eikenboom'},  # noqa
                {'id': 'ID013', 'type': 'Eikenboom', 'GlobalID': '00000000-0000-0000-0000-000000000000',
                 'isReported': False, 'description': 'Eikenboom'},  # noqa
                {'id': 'ID014', 'type': 'Eikenboom', 'GlobalID': '00000000-0000-0000-0000-000000000000',
                 'isReported': False, 'description': 'Eikenboom'},  # noqa
            ],
            'category_url': '/signals/v1/public/terms/categories/openbaar-groen-en-water/sub_categories/eikenprocessierups'  # noqa
        })

        signal = SignalFactory.create(extra_properties=extra_properties,
                                      category_assignment__category=self.category_eikenprocessierups)

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertTrue(signal.is_parent)
        self.assertEqual(signal.children.count(), 8)

    def test_duplicate_extra_properties_for_trees(self):
        extra_properties = copy.deepcopy(self.extra_properties)
        extra_properties.append(self.extra_properties[0])

        signal = SignalFactory.create(extra_properties=extra_properties,
                                      category_assignment__category=self.category_eikenprocessierups)

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertTrue(signal.is_parent)
        self.assertEqual(signal.children.count(), 4)

    def test_no_trees_selected(self):
        signal = SignalFactory.create(extra_properties=None,
                                      category_assignment__category=self.category_eikenprocessierups)

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

    def test_one_tree_selected(self):
        extra_properties = copy.deepcopy(self.extra_properties)
        extra_properties[0]['answer'] = [
            {'id': 'TEST-1', 'type': 'Eikenboom', 'GlobalID': '00000000-0000-0000-0000-000000000000',
             'isReported': False, 'description': 'Eikenboom'},
        ]

        signal = SignalFactory.create(extra_properties=extra_properties,
                                      category_assignment__category=self.category_eikenprocessierups)

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

    def test_too_many_trees_selected(self):
        extra_properties = copy.deepcopy(self.extra_properties)
        extra_properties[0]['answer'] = []

        for x in range(25):
            extra_properties[0]['answer'].append(
                {'id': f'TEST-{x}', 'type': 'Eikenboom', 'GlobalID': '00000000-0000-0000-0000-000000000000',
                 'isReported': False, 'description': 'Eikenboom'},
            )

        signal = SignalFactory.create(extra_properties=extra_properties,
                                      category_assignment__category=self.category_eikenprocessierups)

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
                                      category_assignment__category=self.category_eikenprocessierups,
                                      status__state='i')

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

    @override_settings(FEATURE_FLAGS={
        'AUTOMATICALLY_CREATE_CHILD_SIGNALS_PER_EIKENPROCESSIERUPS_TREE': False,  # Interested in this functionality
    })
    def test_signal_feature_disabled(self):
        extra_properties = copy.deepcopy(self.extra_properties)
        signal = SignalFactory.create(extra_properties=extra_properties,
                                      category_assignment__category=self.category_eikenprocessierups)

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)

    def test_create_children_and_copy_attachments(self):
        extra_properties = copy.deepcopy(self.extra_properties)
        signal = SignalFactoryWithImage.create(extra_properties=extra_properties,
                                               category_assignment__category=self.category_eikenprocessierups)

        attachment_count = signal.attachments.filter(is_image=True).count()

        self.assertFalse(signal.is_parent)
        self.assertEqual(signal.children.count(), 0)
        self.assertEqual(attachment_count, 1)

        AutoCreateChildrenService.run(signal_id=signal.pk)

        signal.refresh_from_db()

        self.assertTrue(signal.is_parent)
        self.assertEqual(signal.children.count(), 4)

        for child in signal.children.all():
            self.assertEqual(child.attachments.filter(is_image=True).count(), attachment_count)
