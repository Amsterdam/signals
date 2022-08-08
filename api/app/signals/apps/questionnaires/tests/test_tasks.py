# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import now
from freezegun import freeze_time

from signals.apps.questionnaires.services.reaction_request import REACTION_REQUEST_DAYS_OPEN
from signals.apps.questionnaires.tasks import clean_up_reaction_request_task
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models.signal import Signal


class TestCleanUpReactionRequested(TestCase):
    def setUp(self):
        with freeze_time(now() - timedelta(days=2 * REACTION_REQUEST_DAYS_OPEN)):
            # Five signals that were in state REACTIE_GEVRAAGD and too old to
            # still receive an update.
            SignalFactory.create_batch(5, status__state=workflow.REACTIE_GEVRAAGD)

        with freeze_time(now() - timedelta(days=REACTION_REQUEST_DAYS_OPEN // 2)):
            # Five signals that were in state REACTIE_GEVRAAGD and may still
            # get an update.
            SignalFactory.create_batch(5, status__state=workflow.REACTIE_GEVRAAGD)

    def test_task(self):
        clean_up_reaction_request_task()
        reactie_gevraagd = Signal.objects.filter(status__state=workflow.REACTIE_GEVRAAGD)
        reactie_ontvangen = Signal.objects.filter(status__state=workflow.REACTIE_ONTVANGEN)
        self.assertEqual(reactie_gevraagd.count(), 5)
        self.assertEqual(reactie_ontvangen.count(), 5)
