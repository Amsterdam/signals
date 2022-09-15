# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.db.models.signals import post_save
from django.test import TestCase, override_settings
from factory.django import mute_signals

from signals.apps.history.models import Log
from signals.apps.history.services import SignalLogService
from signals.apps.signals.factories import SignalFactoryValidLocation
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


@override_settings(FEATURE_FLAGS={'SIGNAL_HISTORY_LOG_ENABLED': True})
class TestBugSIG4789(TestCase):
    """
    When creating a child signal the parent signal has a log item that states that a signal with id was created for
    the parent signal. When translating this action in the history response this was shown as "Actie onbekend." instead
    of "Deelmelding toegevoegd".

    The log action should check if the following:
    - action should be ACTION_CREATE
    - the object_id must be set to the ID of the child signal
    - the _signal_id must be set to the ID of the parent signal
    """
    @mute_signals(post_save, create_initial, update_category_assignment, update_location, update_priority,
                  update_signal_departments, update_status, update_type, update_user_assignment)
    def test_log_create_initial_child_signal(self):
        self.assertEqual(0, Log.objects.count())

        parent_signal = SignalFactoryValidLocation.create()
        child_signal = SignalFactoryValidLocation.create(parent=parent_signal)

        SignalLogService.log_create_initial(child_signal)

        # Check if we have 1 log items on the parent signal
        self.assertEqual(1, parent_signal.history_log.count())

        # Check if we have 5 log items on the child signal
        self.assertEqual(5, child_signal.history_log.count())

        # The parent signal should have a log item for the new child signal that was created
        log = parent_signal.history_log.get(action=Log.ACTION_CREATE, content_type__app_label__iexact='signals',
                                            content_type__model__iexact='signal', object_pk=child_signal.pk)
        self.assertEqual(log.get_action(), 'Deelmelding toegevoegd')
