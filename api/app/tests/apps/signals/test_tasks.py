from django.contrib.gis.geos import Point
from django.test import TransactionTestCase
from django.utils import timezone

from signals.apps.signals import workflow
from signals.apps.signals.models.category_assignment import CategoryAssignment
from signals.apps.signals.models.category_translation import CategoryTranslation
from signals.apps.signals.models.location import STADSDEEL_CENTRUM
from signals.apps.signals.models.priority import Priority
from signals.apps.signals.models.signal import Signal
from tests.apps.signals import factories


class TestTaskTranslateCategory(TransactionTestCase):
    def setUp(self):
        self.test_category_old = factories.CategoryFactory.create()
        self.test_category_old.name = 'old category'
        self.test_category_old.save()
        self.test_category_new = factories.CategoryFactory.create()
        self.test_category_new.name = 'new category'
        self.test_category_new.save()

        # Deserialized data (taken from test_models.py)
        self.signal_data = {
            'text': 'text message',
            'text_extra': 'test message extra',
            'incident_date_start': timezone.now(),
        }
        self.location_data = {
            'geometrie': Point(4.898466, 52.361585),
            'stadsdeel': STADSDEEL_CENTRUM,
            'buurt_code': 'aaa1',
        }
        self.reporter_data = {
            'email': 'test_reporter@example.com',
            'phone': '0123456789',
        }
        self.category_assignment_data = {
            'category': self.test_category_old,
        }
        self.status_data = {
            'state': workflow.GEMELD,
            'text': 'text message',
            'user': 'test@example.com',
        }
        self.priority_data = {
            'priority': Priority.PRIORITY_HIGH,
        }
        self.note_data = {
            'text': 'Dit is een test notitie.',
            'created_by': 'test@example.com',
        }

    def test_translation_happens(self):
        CategoryTranslation.objects.create(
            created_by='somebody@example.com',
            old_category=self.test_category_old,
            new_category=self.test_category_new,
            text='WAAROM? DAAROM!',
        )

        signal = Signal.actions.create_initial(
            signal_data=self.signal_data,
            location_data=self.location_data,
            status_data=self.status_data,
            category_assignment_data=self.category_assignment_data,
            reporter_data=self.reporter_data,
            priority_data=self.priority_data,
        )

        signal.refresh_from_db()
        self.assertEqual(signal.category_assignment.category, self.test_category_new)

        cats = CategoryAssignment.objects.filter(_signal=signal)
        self.assertEqual(cats.count(), 2)

    def test_translation_skipped_category_not_in_translations(self):
        signal = Signal.actions.create_initial(
            signal_data=self.signal_data,
            location_data=self.location_data,
            status_data=self.status_data,
            category_assignment_data=self.category_assignment_data,
            reporter_data=self.reporter_data,
            priority_data=self.priority_data,
        )

        signal.refresh_from_db()
        self.assertEqual(signal.category_assignment.category, self.test_category_old)

        cats = CategoryAssignment.objects.filter(_signal=signal)
        self.assertEqual(cats.count(), 1)

    def test_translation_happens_split(self):
        CategoryTranslation.objects.create(
            created_by='somebody@example.com',
            old_category=self.test_category_old,
            new_category=self.test_category_new,
            text='WAAROM? DAAROM!',
        )

        signal = factories.SignalFactory.create()

        split_data = [
            {
                'text': 'Test',
                'category': {
                    'sub_category': self.test_category_old,
                }
            }
        ]

        signal = Signal.actions.split(split_data=split_data, signal=signal)
        signal.refresh_from_db()

        child_signal = signal.children.first()

        self.assertEqual(child_signal.category_assignment.category, self.test_category_new)

        cats = CategoryAssignment.objects.filter(_signal=child_signal)
        self.assertEqual(cats.count(), 2)

    def test_translation_skipped_category_not_in_translations_split(self):
        signal = factories.SignalFactory.create()

        split_data = [
            {
                'text': 'Test',
                'category': {
                    'sub_category': self.test_category_old,
                }
            }
        ]
        signal = Signal.actions.split(split_data=split_data, signal=signal)
        signal.refresh_from_db()
        child_signal = signal.children.first()

        self.assertEqual(child_signal.category_assignment.category, self.test_category_old)

        cats = CategoryAssignment.objects.filter(_signal=child_signal)
        self.assertEqual(cats.count(), 1)
