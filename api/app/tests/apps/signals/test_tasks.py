from django.contrib.gis.geos import Point
from django.test import TransactionTestCase
from django.utils import timezone

from signals.apps.signals import factories, workflow
from signals.apps.signals.models import Status
from signals.apps.signals.models.category_assignment import CategoryAssignment
from signals.apps.signals.models.category_translation import CategoryTranslation
from signals.apps.signals.models.location import STADSDEEL_CENTRUM
from signals.apps.signals.models.priority import Priority
from signals.apps.signals.models.signal import Signal
from signals.apps.signals.tasks import update_status_children_based_on_parent
from signals.apps.signals.workflow import AFGEHANDELD, AFWACHTING, GEANNULEERD


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


class TestTaskUpdateStatusChildrenBasedOnParent(TransactionTestCase):
    def setUp(self):
        self.parent_signal = factories.SignalFactory.create()
        self.child_signal_1, self.child_signal_2 = factories.SignalFactory.create_batch(2, parent=self.parent_signal)

        self.test_feature_flags_enabled = {
            'API_DETERMINE_STADSDEEL_ENABLED': False,  # we are not interested in search behavior here
            'API_FILTER_EXTRA_PROPERTIES': False,  # we are not interested in search behavior here
            'API_SEARCH_ENABLED': False,  # we are not interested in search behavior here
            'API_TRANSFORM_SOURCE_BASED_ON_REPORTER': False,  # we are not interested in search behavior here
            'API_TRANSFORM_SOURCE_IF_A_SIGNAL_IS_A_CHILD': False,  # we are not interested in search behavior here
            'API_VALIDATE_SOURCE_AGAINST_SOURCE_MODEL': False,  # we are not interested in search behavior here
            'SEARCH_BUILD_INDEX': False,  # we are not interested in search behavior here
            'TASK_UPDATE_CHILDREN_BASED_ON_PARENT': True,  # THIS IS WHAT WE WANT TO TEST
        }
        self.test_feature_flags_disabled = {
            'API_DETERMINE_STADSDEEL_ENABLED': False,  # we are not interested in search behavior here
            'API_FILTER_EXTRA_PROPERTIES': False,  # we are not interested in search behavior here
            'API_SEARCH_ENABLED': False,  # we are not interested in search behavior here
            'API_TRANSFORM_SOURCE_BASED_ON_REPORTER': False,  # we are not interested in search behavior here
            'API_TRANSFORM_SOURCE_IF_A_SIGNAL_IS_A_CHILD': False,  # we are not interested in search behavior here
            'API_VALIDATE_SOURCE_AGAINST_SOURCE_MODEL': False,  # we are not interested in search behavior here
            'SEARCH_BUILD_INDEX': False,  # we are not interested in search behavior here
            'TASK_UPDATE_CHILDREN_BASED_ON_PARENT': False,  # THIS IS WHAT WE WANT TO TEST
        }

    def test_task_feature_disabled(self):
        """
        Feature disabled by FEATURE_FLAG should not trigger the children to status GEANNULEERD
        """
        parent_signal_state = self.parent_signal.status.state
        child_signal_1_state = self.child_signal_1.status.state
        child_signal_2_state = self.child_signal_2.status.state

        status = Status.objects.create(state=AFGEHANDELD, text='Test', _signal=self.parent_signal)
        self.parent_signal.status = status
        self.parent_signal.save()

        with self.settings(FEATURE_FLAGS=self.test_feature_flags_disabled):
            update_status_children_based_on_parent(signal_id=self.parent_signal.id)

        self.parent_signal.refresh_from_db()
        self.child_signal_1.refresh_from_db()
        self.child_signal_2.refresh_from_db()

        self.assertNotEqual(self.parent_signal.status.state, parent_signal_state)
        self.assertEqual(self.parent_signal.status.state, AFGEHANDELD)
        self.assertEqual(self.child_signal_1.status.state, child_signal_1_state)
        self.assertEqual(self.child_signal_2.status.state, child_signal_2_state)

    def test_task_parent_status_not_afgehandeld(self):
        """
        Parent Signal status to any status but AFGEHANDELD should not trigger the children to status GEANNULEERD
        """
        parent_signal_state = self.parent_signal.status.state
        child_signal_1_state = self.child_signal_1.status.state
        child_signal_2_state = self.child_signal_2.status.state

        status = Status.objects.create(state=AFWACHTING, text='Test', _signal=self.parent_signal)
        self.parent_signal.status = status
        self.parent_signal.save()

        with self.settings(FEATURE_FLAGS=self.test_feature_flags_enabled):
            update_status_children_based_on_parent(signal_id=self.parent_signal.id)

        self.parent_signal.refresh_from_db()
        self.child_signal_1.refresh_from_db()
        self.child_signal_2.refresh_from_db()

        self.assertNotEqual(self.parent_signal.status.state, parent_signal_state)
        self.assertEqual(self.parent_signal.status.state, AFWACHTING)
        self.assertEqual(self.child_signal_1.status.state, child_signal_1_state)
        self.assertEqual(self.child_signal_2.status.state, child_signal_2_state)

    def test_task_parent_status_afgehandeld(self):
        """
        Parent Signal status to AFGEHANDELD should trigger the children to status GEANNULEERD
        """
        parent_signal_state = self.parent_signal.status.state
        child_signal_1_state = self.child_signal_1.status.state
        child_signal_2_state = self.child_signal_2.status.state

        status = Status.objects.create(state=AFGEHANDELD, text='Test', _signal=self.parent_signal)
        self.parent_signal.status = status
        self.parent_signal.save()

        with self.settings(FEATURE_FLAGS=self.test_feature_flags_enabled):
            update_status_children_based_on_parent(signal_id=self.parent_signal.id)

        self.parent_signal.refresh_from_db()
        self.child_signal_1.refresh_from_db()
        self.child_signal_2.refresh_from_db()

        self.assertNotEqual(self.parent_signal.status.state, parent_signal_state)
        self.assertEqual(self.parent_signal.status.state, AFGEHANDELD)
        self.assertNotEqual(self.child_signal_1.status.state, child_signal_1_state)
        self.assertEqual(self.child_signal_1.status.state, GEANNULEERD)
        self.assertNotEqual(self.child_signal_2.status.state, child_signal_2_state)
        self.assertEqual(self.child_signal_2.status.state, GEANNULEERD)

    def test_task_child_status_afgehandeld(self):
        """
        Child Signal status to AFGEHANDELD should not trigger the other children to status GEANNULEERD
        """
        parent_signal_state = self.parent_signal.status.state
        child_signal_1_state = self.child_signal_1.status.state
        child_signal_2_state = self.child_signal_2.status.state

        status = Status.objects.create(state=AFGEHANDELD, text='Test', _signal=self.child_signal_1)
        self.child_signal_1.status = status
        self.child_signal_1.save()

        with self.settings(FEATURE_FLAGS=self.test_feature_flags_enabled):
            update_status_children_based_on_parent(signal_id=self.child_signal_1.id)

        self.parent_signal.refresh_from_db()
        self.child_signal_1.refresh_from_db()
        self.child_signal_2.refresh_from_db()

        self.assertEqual(self.parent_signal.status.state, parent_signal_state)
        self.assertNotEqual(self.child_signal_1.status.state, child_signal_1_state)
        self.assertEqual(self.child_signal_1.status.state, AFGEHANDELD)
        self.assertEqual(self.child_signal_2.status.state, child_signal_2_state)
        self.assertNotEqual(self.child_signal_2.status.state, GEANNULEERD)

    def test_signal_receiver_feature_disabled(self):
        """
        Feature disabled by TASK_UPDATE_CHILDREN_BASED_ON_PARENT should not trigger the children to status GEANNULEERD
        """
        parent_signal_state = self.parent_signal.status.state
        child_signal_1_state = self.child_signal_1.status.state
        child_signal_2_state = self.child_signal_2.status.state

        with self.settings(FEATURE_FLAGS=self.test_feature_flags_disabled):
            data = dict(state=AFGEHANDELD, text='Test')
            Signal.actions.update_status(data, signal=self.parent_signal)

        self.parent_signal.refresh_from_db()
        self.child_signal_1.refresh_from_db()
        self.child_signal_2.refresh_from_db()

        self.assertNotEqual(self.parent_signal.status.state, parent_signal_state)
        self.assertEqual(self.parent_signal.status.state, AFGEHANDELD)
        self.assertEqual(self.child_signal_1.status.state, child_signal_1_state)
        self.assertEqual(self.child_signal_2.status.state, child_signal_2_state)

    def test_signal_receiver_parent_status_not_afgehandeld(self):
        """
        Parent Signal status to any status but AFGEHANDELD should not trigger the children to status GEANNULEERD
        """
        parent_signal_state = self.parent_signal.status.state
        child_signal_1_state = self.child_signal_1.status.state
        child_signal_2_state = self.child_signal_2.status.state

        with self.settings(FEATURE_FLAGS=self.test_feature_flags_enabled):
            data = dict(state=AFWACHTING, text='Test')
            Signal.actions.update_status(data, signal=self.parent_signal)

        self.parent_signal.refresh_from_db()
        self.child_signal_1.refresh_from_db()
        self.child_signal_2.refresh_from_db()

        self.assertNotEqual(self.parent_signal.status.state, parent_signal_state)
        self.assertEqual(self.parent_signal.status.state, AFWACHTING)
        self.assertEqual(self.child_signal_1.status.state, child_signal_1_state)
        self.assertEqual(self.child_signal_2.status.state, child_signal_2_state)

    def test_signal_receiver_parent_status_afgehandeld(self):
        """
        Parent Signal status to AFGEHANDELD should trigger the children to status GEANNULEERD
        """
        parent_signal_state = self.parent_signal.status.state
        child_signal_1_state = self.child_signal_1.status.state
        child_signal_2_state = self.child_signal_2.status.state

        with self.settings(FEATURE_FLAGS=self.test_feature_flags_enabled):
            data = dict(state=AFGEHANDELD, text='Test')
            Signal.actions.update_status(data, signal=self.parent_signal)

        self.parent_signal.refresh_from_db()
        self.child_signal_1.refresh_from_db()
        self.child_signal_2.refresh_from_db()

        self.assertNotEqual(self.parent_signal.status.state, parent_signal_state)
        self.assertEqual(self.parent_signal.status.state, AFGEHANDELD)
        self.assertNotEqual(self.child_signal_1.status.state, child_signal_1_state)
        self.assertEqual(self.child_signal_1.status.state, GEANNULEERD)
        self.assertNotEqual(self.child_signal_2.status.state, child_signal_2_state)
        self.assertEqual(self.child_signal_2.status.state, GEANNULEERD)

    def test_signal_receiver_child_status_afgehandeld(self):
        """
        Child Signal status to AFGEHANDELD should not trigger the other children to status GEANNULEERD
        """
        parent_signal_state = self.parent_signal.status.state
        child_signal_1_state = self.child_signal_1.status.state
        child_signal_2_state = self.child_signal_2.status.state

        with self.settings(FEATURE_FLAGS=self.test_feature_flags_enabled):
            data = dict(state=AFGEHANDELD, text='Test')
            Signal.actions.update_status(data, signal=self.child_signal_1)

        self.parent_signal.refresh_from_db()
        self.child_signal_1.refresh_from_db()
        self.child_signal_2.refresh_from_db()

        self.assertEqual(self.parent_signal.status.state, parent_signal_state)
        self.assertNotEqual(self.child_signal_1.status.state, child_signal_1_state)
        self.assertEqual(self.child_signal_1.status.state, AFGEHANDELD)
        self.assertEqual(self.child_signal_2.status.state, child_signal_2_state)
        self.assertNotEqual(self.child_signal_2.status.state, GEANNULEERD)

    def test_task_parent_status_geannuleerd(self):
        """
        Parent Signal status to GEANNULEERD should trigger the children to status GEANNULEERD
        """
        parent_signal_state = self.parent_signal.status.state
        child_signal_1_state = self.child_signal_1.status.state
        child_signal_2_state = self.child_signal_2.status.state

        status = Status.objects.create(state=GEANNULEERD, text='Test', _signal=self.parent_signal)
        self.parent_signal.status = status
        self.parent_signal.save()

        with self.settings(FEATURE_FLAGS=self.test_feature_flags_enabled):
            update_status_children_based_on_parent(signal_id=self.parent_signal.id)

        self.parent_signal.refresh_from_db()
        self.child_signal_1.refresh_from_db()
        self.child_signal_2.refresh_from_db()

        self.assertNotEqual(self.parent_signal.status.state, parent_signal_state)
        self.assertEqual(self.parent_signal.status.state, GEANNULEERD)
        self.assertNotEqual(self.child_signal_1.status.state, child_signal_1_state)
        self.assertEqual(self.child_signal_1.status.state, GEANNULEERD)
        self.assertNotEqual(self.child_signal_2.status.state, child_signal_2_state)
        self.assertEqual(self.child_signal_2.status.state, GEANNULEERD)
