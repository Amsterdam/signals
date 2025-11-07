# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam
from django.db.models.signals import post_save
from django.test import TestCase, override_settings
from django.utils import timezone
from factory.django import mute_signals

from signals.apps.feedback.factories import FeedbackFactory
from signals.apps.history.models import Log
from signals.apps.history.services import SignalLogService
from signals.apps.questionnaires.factories import QuestionnaireFactory, SessionFactory
from signals.apps.questionnaires.models import Questionnaire
from signals.apps.signals.factories import (
    CategoryAssignmentFactory,
    DepartmentFactory,
    LocationFactory,
    NoteFactory,
    PriorityFactory,
    SignalDepartmentsFactory,
    SignalFactoryValidLocation,
    SignalUserFactory,
    StatusFactory,
    StoredSignalFilterFactory,
    TypeFactory
)
from signals.apps.signals.managers import (
    create_initial,
    update_category_assignment,
    update_location,
    update_priority,
    update_signal_departments,
    update_status,
    update_type,
    update_user_assignment
)


class AssertSignalsNotInLogMixin:
    def assertSignalsNotInLog(self, signals):
        """
        Used to validate if the given signals have no log rules
        """
        for signal in signals:
            self.assertEqual(0, signal.history_log.count())
            self.assertEqual(0, Log.objects.filter(content_type__app_label__iexact='signals',
                                                   content_type__model__iexact='signal',
                                                   object_pk=signal.pk).count())


@override_settings(FEATURE_FLAGS={
    'API_DETERMINE_STADSDEEL_ENABLED': False,
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER': False,
})
class TestLogSignalLogService(AssertSignalsNotInLogMixin, TestCase):
    """
    Simple test case to check if logs are created using the SignalLogService
    """
    def setUp(self) -> None:
        self.signal = SignalFactoryValidLocation.create()

        # Some Signals that should not have and get any log rules during these tests
        self.signals_no_log = SignalFactoryValidLocation.create_batch(4)

    @mute_signals(post_save, create_initial, update_category_assignment, update_location, update_priority,
                  update_signal_departments, update_status, update_type, update_user_assignment)
    def test_log_create_initial(self) -> None:
        self.assertEqual(0, Log.objects.count())

        SignalLogService.log_create_initial(self.signal)

        self.assertSignalsNotInLog(self.signals_no_log)

        self.assertEqual(5, Log.objects.count())
        self.assertEqual(5, self.signal.history_log.count())
        self.assertEqual(0, self.signal.history_log.exclude(action=Log.ACTION_UPDATE).count())
        self.assertEqual(5, self.signal.history_log.filter(action=Log.ACTION_UPDATE).count())

    @mute_signals(post_save, update_category_assignment, update_location, update_priority,
                  update_signal_departments, update_status, update_type, update_user_assignment)
    def test_parent_updated_when_log_create_initial_with_child(self) -> None:
        current_updated_at = self.signal.updated_at
        child_signal = SignalFactoryValidLocation.create(parent=self.signal)

        SignalLogService.log_create_initial(child_signal)

        self.signal.refresh_from_db()
        new_updated_at = self.signal.updated_at
        assert current_updated_at < new_updated_at

    @mute_signals(post_save, create_initial, update_category_assignment, update_location, update_priority,
                  update_signal_departments, update_status, update_type, update_user_assignment)
    def test_log_create_note(self) -> None:
        self.assertEqual(0, Log.objects.count())

        note = NoteFactory.create(_signal=self.signal)
        SignalLogService.log_create_note(note)

        self.assertSignalsNotInLog(self.signals_no_log)

        self.assertEqual(1, Log.objects.count())
        self.assertEqual(1, self.signal.history_log.count())
        self.assertEqual(0, self.signal.history_log.exclude(action=Log.ACTION_CREATE).count())
        self.assertEqual(1, self.signal.history_log.filter(action=Log.ACTION_CREATE).count())
        self.assertEqual(1, note.history_log.count())

    @mute_signals(post_save, create_initial, update_category_assignment, update_location, update_priority,
                  update_signal_departments, update_status, update_type, update_user_assignment)
    def test_log_update_category_assignment(self) -> None:
        self.assertEqual(0, Log.objects.count())

        category_assignment = CategoryAssignmentFactory.create(_signal=self.signal)
        SignalLogService.log_update_category_assignment(category_assignment)

        self.assertSignalsNotInLog(self.signals_no_log)

        self.assertEqual(1, Log.objects.count())
        self.assertEqual(1, self.signal.history_log.count())
        self.assertEqual(0, self.signal.history_log.exclude(action=Log.ACTION_UPDATE).count())
        self.assertEqual(1, self.signal.history_log.filter(action=Log.ACTION_UPDATE).count())
        self.assertEqual(1, category_assignment.history_log.count())

    @mute_signals(post_save, create_initial, update_category_assignment, update_location, update_priority,
                  update_signal_departments, update_status, update_type, update_user_assignment)
    def test_log_update_location(self) -> None:
        self.assertEqual(0, Log.objects.count())

        location = LocationFactory.create(_signal=self.signal)
        SignalLogService.log_update_location(location)

        self.assertSignalsNotInLog(self.signals_no_log)

        self.assertEqual(1, Log.objects.count())
        self.assertEqual(1, self.signal.history_log.count())
        self.assertEqual(0, self.signal.history_log.exclude(action=Log.ACTION_UPDATE).count())
        self.assertEqual(1, self.signal.history_log.filter(action=Log.ACTION_UPDATE).count())
        self.assertEqual(1, location.history_log.count())

    @mute_signals(post_save, create_initial, update_category_assignment, update_location, update_priority,
                  update_signal_departments, update_status, update_type, update_user_assignment)
    def test_log_update_priority(self) -> None:
        self.assertEqual(0, Log.objects.count())

        priority = PriorityFactory.create(_signal=self.signal)
        SignalLogService.log_update_priority(priority)

        self.assertSignalsNotInLog(self.signals_no_log)

        self.assertEqual(1, Log.objects.count())
        self.assertEqual(1, self.signal.history_log.count())
        self.assertEqual(0, self.signal.history_log.exclude(action=Log.ACTION_UPDATE).count())
        self.assertEqual(1, self.signal.history_log.filter(action=Log.ACTION_UPDATE).count())
        self.assertEqual(1, priority.history_log.count())

    @mute_signals(post_save, create_initial, update_category_assignment, update_location, update_priority,
                  update_signal_departments, update_status, update_type, update_user_assignment)
    def test_log_update_status(self) -> None:
        self.assertEqual(0, Log.objects.count())

        status = StatusFactory.create(_signal=self.signal)
        SignalLogService.log_update_status(status)

        self.assertSignalsNotInLog(self.signals_no_log)

        self.assertEqual(1, Log.objects.count())
        self.assertEqual(1, self.signal.history_log.count())
        self.assertEqual(0, self.signal.history_log.exclude(action=Log.ACTION_UPDATE).count())
        self.assertEqual(1, self.signal.history_log.filter(action=Log.ACTION_UPDATE).count())
        self.assertEqual(1, status.history_log.count())

    @mute_signals(post_save, create_initial, update_category_assignment, update_location, update_priority,
                  update_signal_departments, update_status, update_type, update_user_assignment)
    def test_log_update_type(self) -> None:
        self.assertEqual(0, Log.objects.count())

        _type = TypeFactory.create(_signal=self.signal)
        SignalLogService.log_update_type(_type)

        self.assertSignalsNotInLog(self.signals_no_log)

        self.assertEqual(1, Log.objects.count())
        self.assertEqual(1, self.signal.history_log.count())
        self.assertEqual(0, self.signal.history_log.exclude(action=Log.ACTION_UPDATE).count())
        self.assertEqual(1, self.signal.history_log.filter(action=Log.ACTION_UPDATE).count())
        self.assertEqual(1, _type.history_log.count())

    @mute_signals(post_save, create_initial, update_category_assignment, update_location, update_priority,
                  update_signal_departments, update_status, update_type, update_user_assignment)
    def test_update_user_assignment(self) -> None:
        self.assertEqual(0, Log.objects.count())

        user_assignment = SignalUserFactory.create(_signal=self.signal)
        SignalLogService.log_update_user_assignment(user_assignment)

        self.assertSignalsNotInLog(self.signals_no_log)

        self.assertEqual(1, Log.objects.count())
        self.assertEqual(1, self.signal.history_log.count())
        self.assertEqual(1, user_assignment.history_log.count())

    @mute_signals(post_save, create_initial, update_category_assignment, update_location, update_priority,
                  update_signal_departments, update_status, update_type, update_user_assignment)
    def test_update_signal_departments(self) -> None:
        self.assertEqual(0, Log.objects.count())

        signal_departments = SignalDepartmentsFactory.create(_signal=self.signal)

        departments = DepartmentFactory.create_batch(5)
        signal_departments.departments.add(*departments)
        signal_departments.save()

        SignalLogService.log_update_signal_departments(signal_departments)

        self.assertSignalsNotInLog(self.signals_no_log)

        self.assertEqual(1, Log.objects.count())
        self.assertEqual(1, self.signal.history_log.count())
        self.assertEqual(1, signal_departments.history_log.count())

    @mute_signals(post_save, create_initial, update_category_assignment, update_location, update_priority,
                  update_signal_departments, update_status, update_type, update_user_assignment)
    def test_a_model_no_related_to_a_signal(self) -> None:
        self.assertEqual(0, Log.objects.count())

        stored_signal_filter = StoredSignalFilterFactory.create()
        Log.objects.create(action=Log.ACTION_CREATE, extra=stored_signal_filter.id, object=stored_signal_filter,
                           created_at=timezone.now())

        self.assertEqual(1, Log.objects.count())
        self.assertEqual(1, Log.objects.filter(content_type__app_label__iexact='signals',
                                               content_type__model__iexact='storedsignalfilter').count())
        self.assertEqual(0, Log.objects.filter(_signal_id__isnull=False).count())
        self.assertSignalsNotInLog(self.signals_no_log + [self.signal])

    @mute_signals(post_save, create_initial, update_category_assignment, update_location, update_priority,
                  update_signal_departments, update_status, update_type, update_user_assignment)
    def test_log_signal_delete(self) -> None:
        self.assertEqual(0, Log.objects.count())

        SignalLogService.log_create_initial(self.signal)

        self.assertSignalsNotInLog(self.signals_no_log)

        self.assertEqual(5, Log.objects.count())
        self.assertEqual(5, self.signal.history_log.count())

        self.signal.delete()

        self.assertEqual(0, Log.objects.count())

    @mute_signals(post_save, create_initial, update_category_assignment, update_location, update_priority,
                  update_signal_departments, update_status, update_type, update_user_assignment)
    def test_log_receive_feedback(self) -> None:
        now = timezone.now()
        current_updated_at = self.signal.updated_at

        self.assertEqual(0, Log.objects.count())

        SignalLogService.log_create_initial(self.signal)

        self.assertSignalsNotInLog(self.signals_no_log)

        self.assertEqual(5, Log.objects.count())
        self.assertEqual(5, self.signal.history_log.count())

        feedback = FeedbackFactory.create(_signal=self.signal, submitted_at=now)
        SignalLogService.log_receive_feedback(feedback)

        self.signal.refresh_from_db()
        new_updated_at = self.signal.updated_at

        assert current_updated_at < new_updated_at

        self.assertEqual(6, Log.objects.count())

    @mute_signals(post_save, create_initial, update_category_assignment, update_location, update_priority,
                  update_signal_departments, update_status, update_type, update_user_assignment)
    def test_log_external_reaction_received(self) -> None:
        current_updated_at = self.signal.updated_at

        self.assertEqual(0, Log.objects.count())

        SignalLogService.log_create_initial(self.signal)

        self.assertSignalsNotInLog(self.signals_no_log)

        self.assertEqual(5, Log.objects.count())
        self.assertEqual(5, self.signal.history_log.count())

        questionnaire = QuestionnaireFactory.create(flow=Questionnaire.FORWARD_TO_EXTERNAL)

        session = SessionFactory.create(_signal=self.signal, questionnaire=questionnaire)
        session.frozen = True

        SignalLogService.log_external_reaction_received(session=session, reaction="Super good!")

        self.signal.refresh_from_db()
        new_updated_at = self.signal.updated_at

        assert current_updated_at < new_updated_at

        self.assertEqual(6, Log.objects.count())

    @mute_signals(post_save, create_initial, update_category_assignment, update_location, update_priority,
                  update_signal_departments, update_status, update_type, update_user_assignment)
    def test_log_external_reaction_not_received(self) -> None:
        current_updated_at = self.signal.updated_at

        self.assertEqual(0, Log.objects.count())

        SignalLogService.log_create_initial(self.signal)

        self.assertSignalsNotInLog(self.signals_no_log)

        self.assertEqual(5, Log.objects.count())
        self.assertEqual(5, self.signal.history_log.count())

        questionnaire = QuestionnaireFactory.create(flow=Questionnaire.FORWARD_TO_EXTERNAL)

        session = SessionFactory.create(_signal=self.signal, questionnaire=questionnaire)
        session.save()

        SignalLogService.log_external_reaction_not_received(session=session)

        self.signal.refresh_from_db()
        new_updated_at = self.signal.updated_at

        assert current_updated_at < new_updated_at

        self.assertEqual(6, Log.objects.count())
