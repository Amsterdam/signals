from django.test import TransactionTestCase

from signals.apps.signals import factories
from signals.apps.signals.models import Status
from signals.apps.signals.models.signal import Signal
from signals.apps.signals.tasks import update_status_children_based_on_parent
from signals.apps.signals.workflow import AFGEHANDELD, AFWACHTING, GEANNULEERD


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
