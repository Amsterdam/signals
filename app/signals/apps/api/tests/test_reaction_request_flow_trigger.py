# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
"""
Test REST API trigger for reaction request flow.

Reaction request flow is triggered through a status update to REACTIE_GEVRAAGD.
This transition is tested here. Checks fix for SIG-3887.
"""
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory
from signals.test.utils import SignalsBaseApiTestCase


class TestReactionRequestFlowTrigger(SignalsBaseApiTestCase):
    detail_endpoint = '/signals/v1/private/signals/{pk}'

    def setUp(self):
        self.signal = SignalFactory.create(status__state=workflow.GEMELD)
        self.client.force_authenticate(user=self.superuser)

        payload = {'status': {'state': workflow.REACTIE_GEVRAAGD, 'text': 'Our question.'}}
        response = self.client.patch(f'/signals/v1/private/signals/{self.signal.pk}', data=payload, format='json')

        self.assertEqual(response.status_code, 200)

    def test_email_unknown_no_REACTIE_GEVRAAGD_state_allowed(self):
        self.signal.reporter.email = None
        self.signal.reporter.save()
        self.signal.refresh_from_db()

        payload = {'status': {'state': workflow.REACTIE_GEVRAAGD, 'text': 'Our question.'}}
        response = self.client.patch(f'/signals/v1/private/signals/{self.signal.pk}', data=payload, format='json')

        self.assertEqual(response.status_code, 400)

    def test_update_status_more_than_1000_characters(self):
        text = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut
labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip
ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat
nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est
laborum. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et
dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. Lorem
ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur
sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""
        data = {
            'status': {
                'text': text,
                'state': 'reaction requested'
            }
        }

        response = self.client.patch(f'/signals/v1/private/signals/{self.signal.pk}', data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status']['text'][0],
                         f'Zorg dat deze waarde niet meer dan 1000 tekens bevat (het zijn er nu {len(text)}).')
