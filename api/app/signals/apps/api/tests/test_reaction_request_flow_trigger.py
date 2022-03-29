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

    def test_SIG_4511_update_status_more_than_400_characters(self):
        data = {
            'status': {
                'text': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut '
                        'labore et dolore magna aliqua. Morbi tristique senectus et netus et malesuada fames. '
                        'Vestibulum rhoncus est pellentesque elit ullamcorper dignissim cras tincidunt lobortis. Vitae '
                        'auctor eu augue ut lectus arcu bibendum at varius. Luctus venenatis lectus magna fringilla '
                        'urna. Adipiscing commodo elit at imperdiet dui accumsan sit. Venenatis urna cursus eget nunc '
                        'scelerisque viverra mauris in. Aliquam sem et tortor consequat id porta. Massa enim nec dui '
                        'nunc. Pellentesque adipiscing commodo elit at imperdiet dui accumsan sit.',
                'state': 'reaction requested'
            }
        }

        response = self.client.patch(f'/signals/v1/private/signals/{self.signal.pk}', data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status']['text'][0],
                         'Zorg dat deze waarde niet meer dan 400 tekens bevat (het zijn er nu '
                         f'{len(data["status"]["text"])}).')
