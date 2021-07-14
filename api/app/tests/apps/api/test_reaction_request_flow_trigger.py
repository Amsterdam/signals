# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
"""
Test REST API trigger for reaction request flow.

Reaction request flow is triggered through a status update to REACTIE_GEVRAAGD.
This transition is tested here. Checks fix for SIG-3887.
"""
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory
from tests.test import SignalsBaseApiTestCase


class TestReactionRequestFlowTrigger(SignalsBaseApiTestCase):
    detail_endpoint = '/signals/v1/private/signals/{pk}'

    def setUp(self):
        self.signal = SignalFactory.create(status__state=workflow.GEMELD)
        self.client.force_authenticate(user=self.superuser)

    def test_email_known_REACTIE_GEVRAAGD_state_allowed(self):
        url = self.detail_endpoint.format(pk=self.signal.id)
        payload = {'status': {'state': workflow.REACTIE_GEVRAAGD, 'text': 'Our question.'}}
        response = self.client.patch(url, data=payload, format='json')

        self.assertEqual(response.status_code, 200)

    def test_email_unknown_no_REACTIE_GEVRAAGD_state_allowed(self):
        self.signal.reporter.email = None
        self.signal.reporter.save()
        self.signal.refresh_from_db()

        url = self.detail_endpoint.format(pk=self.signal.id)
        payload = {'status': {'state': workflow.REACTIE_GEVRAAGD, 'text': 'Our question.'}}
        response = self.client.patch(url, data=payload, format='json')

        self.assertEqual(response.status_code, 400)
