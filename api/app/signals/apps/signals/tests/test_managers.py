# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from unittest.mock import patch

from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.core.exceptions import ValidationError
from django.test import TestCase

from signals.apps.signals.factories import AreaFactory, CategoryFactory, SignalFactory
from signals.apps.signals.models import CategoryAssignment, Signal, Type


class TestSignalManager(TestCase):

    def setUp(self):
        self.signal = SignalFactory()
        self.category = CategoryFactory()
        self.category_assignment = CategoryAssignment.objects.create(category=self.category,
                                                                     _signal_id=self.signal.id)

        self.link_category = '/signals/v1/public/terms/categories/{}/sub_categories/{}'.format(
            self.category.parent.slug, self.category.slug
        )
        geometry = MultiPolygon([Polygon.from_bbox([4.877157, 52.357204, 4.929686, 52.385239])], srid=4326)
        self.pt_in_center = Point(4.88, 52.36)
        self.pt_out_center = Point(6, 53)
        self.area = AreaFactory.create(geometry=geometry, name='Centrum', code='centrum', _type__code='district')

    @patch('signals.apps.signals.models.CategoryAssignment.objects.create')
    def test_update_category_assignment(self, cat_assignment_create):
        cat_assignment_create.return_value = self.category_assignment

        Signal.actions.update_category_assignment({'category': self.category}, self.signal)

        # Should create an assignment
        cat_assignment_create.assert_called_once()
        cat_assignment_create.reset_mock()

        self.signal.refresh_from_db()
        Signal.actions.update_category_assignment({'category': self.category}, self.signal)

        # Update with the same category should not create a new assignment
        cat_assignment_create.assert_not_called()

    def test_update_category_assignment_invalid_data(self):
        with self.assertRaises(ValidationError) as ve:
            Signal.actions.update_category_assignment({'yrogetac': self.category}, self.signal)

        self.assertEqual(ve.exception.message, 'Category not found in data')

    def test_update_multiple_invalid_category_data(self):
        with self.assertRaises(ValidationError) as ve:
            Signal.actions.update_multiple(
                {'category_assignment': {'yrogetac': self.category}},
                self.signal
            )

        self.assertEqual(ve.exception.message, 'Category not found in data')

    def test_create_initial_default_type(self):
        signal_data = {
            'text': 'Bladiebla',
            'text_extra': 'Meer bladiebla',
            'incident_date_start': '2020-02-26T12:00:00.000000Z',
            'source': 'online',
        }
        location_data = {
            'geometrie': Point(4.90022563, 52.36768424)
        }
        category_assignment_data = {
            'category': self.category
        }
        status_data = {}  # Default status
        reporter_data = {}  # No reporter
        priority_data = None  # Default priority
        type_data = None  # This triggers the default Type

        signal = Signal.actions.create_initial(signal_data=signal_data,
                                               location_data=location_data,
                                               status_data=status_data,
                                               category_assignment_data=category_assignment_data,
                                               reporter_data=reporter_data,
                                               priority_data=priority_data,
                                               type_data=type_data)

        self.assertEqual(signal.types.count(), 1)
        self.assertIsNotNone(signal.type_assignment)
        self.assertEqual(signal.type_assignment.name, Type.SIGNAL)  # Default is SIGNAL

    def test_create_initial_set_type(self):
        signal_data = {
            'text': 'Is het type nu QUESTION?',
            'incident_date_start': '2020-02-26T12:00:00.000000Z',
            'source': 'online',
        }
        location_data = {
            'geometrie': Point(4.90022563, 52.36768424)
        }
        category_assignment_data = {
            'category': self.category
        }
        type_data = {
            'name': Type.QUESTION
        }
        status_data = {}  # Default status
        reporter_data = {}  # No reporter
        priority_data = None  # Default priority

        signal = Signal.actions.create_initial(signal_data=signal_data,
                                               location_data=location_data,
                                               status_data=status_data,
                                               category_assignment_data=category_assignment_data,
                                               reporter_data=reporter_data,
                                               priority_data=priority_data,
                                               type_data=type_data)

        self.assertEqual(signal.types.count(), 1)
        self.assertIsNotNone(signal.type_assignment)
        self.assertEqual(signal.type_assignment.name, Type.QUESTION)  # Should be QUESTION

    def test_create_initial_inside_default_area(self):
        signal_data = {
            'text': 'Bladiebla',
            'text_extra': 'Meer bladiebla',
            'incident_date_start': '2020-02-26T12:00:00.000000Z',
            'source': 'online',
        }
        location_data = {
            'geometrie': self.pt_in_center
        }
        category_assignment_data = {
            'category': self.category
        }
        status_data = {}  # Default status
        reporter_data = {}  # No reporter
        priority_data = None  # Default priority
        type_data = None  # This triggers the default Type

        signal = Signal.actions.create_initial(signal_data=signal_data,
                                               location_data=location_data,
                                               status_data=status_data,
                                               category_assignment_data=category_assignment_data,
                                               reporter_data=reporter_data,
                                               priority_data=priority_data,
                                               type_data=type_data)

        self.assertEqual(signal.location.area_type_code, self.area._type.code)
        self.assertEqual(signal.location.area_code, self.area.code)
        location_data = {
            "geometrie": self.pt_out_center,
            "buurt_code": "ABCD",
        }
        updated_location = Signal.actions.update_location(location_data, signal)
        self.assertFalse(updated_location.area_type_code)
        self.assertFalse(updated_location.area_code)

    def test_create_initial_outside_default_area(self):
        signal_data = {
            'text': 'Bladiebla',
            'text_extra': 'Meer bladiebla',
            'incident_date_start': '2020-02-26T12:00:00.000000Z',
            'source': 'online',
        }
        location_data = {
            'geometrie': self.pt_out_center
        }
        category_assignment_data = {
            'category': self.category
        }
        status_data = {}  # Default status
        reporter_data = {}  # No reporter
        priority_data = None  # Default priority
        type_data = None  # This triggers the default Type

        signal = Signal.actions.create_initial(signal_data=signal_data,
                                               location_data=location_data,
                                               status_data=status_data,
                                               category_assignment_data=category_assignment_data,
                                               reporter_data=reporter_data,
                                               priority_data=priority_data,
                                               type_data=type_data)

        self.assertFalse(signal.location.area_type_code)
        self.assertFalse(signal.location.area_code)
        location_data = {
            "geometrie": self.pt_in_center,
            "buurt_code": "ABCD",
        }
        updated_location = Signal.actions.update_location(location_data, signal)
        self.assertEqual(updated_location.area_type_code, self.area._type.code)
        self.assertEqual(updated_location.area_code, self.area.code)

    def test_update_type(self):
        type_data = {'name': Type.QUESTION}
        Signal.actions.update_type(data=type_data, signal=self.signal)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.types.count(), 2)
        self.assertIsNotNone(self.signal.type_assignment)
        self.assertEqual(self.signal.type_assignment.name, Type.QUESTION)

        type_data = {'name': Type.SIGNAL}
        Signal.actions.update_type(data=type_data, signal=self.signal)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.types.count(), 3)
        self.assertIsNotNone(self.signal.type_assignment)
        self.assertEqual(self.signal.type_assignment.name, Type.SIGNAL)

    def test_update_type_default(self):
        type_data = {}
        Signal.actions.update_type(data=type_data, signal=self.signal)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.types.count(), 2)
        self.assertIsNotNone(self.signal.type_assignment)
        self.assertEqual(self.signal.type_assignment.name, Type.SIGNAL)
