# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.contrib.auth.models import Permission

from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.feedback.models import Feedback
from signals.apps.questionnaires.models import Questionnaire
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactoryValidLocation, StatusFactory
from signals.test.utils import SIAReadUserMixin, SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestPrivateSignalEmailPreview(SIAReadUserMixin, SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    def setUp(self):
        self.signal = SignalFactoryValidLocation.create()

        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_write_user)

        # 2 templates for the special cases where there are URL's in the body. All other templates will use the fallback
        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD,
                                     title='Uw melding {{ signal_id }}'
                                           f' {EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD}',
                                     body='{{ text }} {{ created_at }} {{ status_text }} {{ positive_feedback_url }} '
                                          '{{ negative_feedback_url }}{{ ORGANIZATION_NAME }}')
        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_GEVRAAGD,
                                     title='Uw melding {{ signal_id }}'
                                           f' {EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_GEVRAAGD}',
                                     body='{{ text }} {{ created_at }} {{ status_text }} {{ reaction_url }} '
                                          '{{ ORGANIZATION_NAME }}')

    def test_get_email_preview_status_reactie_gevraagd(self):
        # Make sure there are no questionnaire objects in the database
        self.assertEqual(Questionnaire.objects.count(), 0)

        currently_set_status = self.signal.status
        status_count = self.signal.statuses.count()

        text = f'Lorem ipsum {workflow.REACTIE_GEVRAAGD} ...'
        endpoint = f'/signals/v1/private/signals/{self.signal.id}/email/preview/' \
                   f'?status={workflow.REACTIE_GEVRAAGD}&text={text}'

        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(f'Uw melding {self.signal.id} {EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_GEVRAAGD}',
                         response_data['subject'])
        self.assertIn(text, response_data['html'])

        # assert that the reactie gevraagd link is in the preview
        self.assertIn('incident/reactie/00000000-0000-0000-0000-000000000000', response_data['html'])

        # Refresh the Signal
        self.signal.refresh_from_db()

        # The same status should be set as before
        self.assertEqual(currently_set_status.id, self.signal.status.id)
        self.assertEqual(currently_set_status.state, self.signal.status.state)
        self.assertEqual(currently_set_status.text, self.signal.status.text)
        self.assertEqual(currently_set_status.send_email, self.signal.status.send_email)

        # no new notes are added to the signal
        self.assertEqual(self.signal.statuses.count(), status_count)

        # no questionnaire object should have been made
        self.assertEqual(Questionnaire.objects.count(), 0)

    def test_get_email_preview_status_handled(self):
        # Make sure there are no feedback objects in the database
        self.assertEqual(Feedback.objects.count(), 0)

        currently_set_status = self.signal.status
        status_count = self.signal.statuses.count()

        text = f'Lorem ipsum {workflow.AFGEHANDELD} ...'
        endpoint = f'/signals/v1/private/signals/{self.signal.id}/email/preview/' \
                   f'?status={workflow.AFGEHANDELD}&text={text}'

        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(f'Uw melding {self.signal.id} {EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD}',
                         response_data['subject'])
        self.assertIn(text, response_data['html'])

        # assert that the KTO links are in the preview
        self.assertIn('kto/ja/00000000-0000-0000-0000-000000000000', response_data['html'])
        self.assertIn('kto/nee/00000000-0000-0000-0000-000000000000', response_data['html'])

        # Refresh the Signal
        self.signal.refresh_from_db()

        # The same status should be set as before
        self.assertEqual(currently_set_status.id, self.signal.status.id)
        self.assertEqual(currently_set_status.state, self.signal.status.state)
        self.assertEqual(currently_set_status.text, self.signal.status.text)
        self.assertEqual(currently_set_status.send_email, self.signal.status.send_email)

        # no new notes are added to the signal
        self.assertEqual(self.signal.statuses.count(), status_count)

        # no feedback object should have been made
        self.assertEqual(Feedback.objects.count(), 0)

    def test_get_email_preview_status(self):
        currently_set_status = self.signal.status
        status_count = self.signal.statuses.count()

        for new_status in [workflow.GEMELD, workflow.AFWACHTING, workflow.BEHANDELING, workflow.GEANNULEERD, ]:
            text = f'Lorem ipsum {new_status} ...'
            endpoint = f'/signals/v1/private/signals/{self.signal.id}/email/preview/' \
                       f'?status={new_status}&text={text}'

            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)

            response_data = response.json()
            self.assertEqual(f'Meer over uw melding {self.signal.id}', response_data['subject'])
            self.assertIn(text, response_data['html'])

            # Refresh the Signal
            self.signal.refresh_from_db()

            # The same status should be set as before
            self.assertEqual(currently_set_status.id, self.signal.status.id)
            self.assertEqual(currently_set_status.state, self.signal.status.state)
            self.assertEqual(currently_set_status.text, self.signal.status.text)
            self.assertEqual(currently_set_status.send_email, self.signal.status.send_email)

            # no new notes are added to the signal
            self.assertEqual(self.signal.statuses.count(), status_count)

        # We need to test workflow.VERZOEK_TOT_AFHANDELING seperatly because we cannot transition to this state from
        # the state GEMELD

        status = StatusFactory.create(_signal=self.signal, state=workflow.AFWACHTING)
        self.signal.status = status
        self.signal.save()

        status_count = self.signal.statuses.count()

        text = f'Lorem ipsum {workflow.VERZOEK_TOT_AFHANDELING} ...'
        endpoint = f'/signals/v1/private/signals/{self.signal.id}/email/preview/' \
                   f'?status={workflow.VERZOEK_TOT_AFHANDELING}&text={text}'

        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(f'Meer over uw melding {self.signal.id}', response_data['subject'])
        self.assertIn(text, response_data['html'])

        # Refresh the Signal
        self.signal.refresh_from_db()

        # The same status should be set as before
        self.assertEqual(status.id, self.signal.status.id)
        self.assertEqual(status.state, self.signal.status.state)
        self.assertEqual(status.text, self.signal.status.text)
        self.assertEqual(status.send_email, self.signal.status.send_email)

        # no new notes are added to the signal
        self.assertEqual(self.signal.statuses.count(), status_count)

    def test_no_email_preview_available(self):
        # From GEMELD to REACTIE_ONTVANGEN is not allowed therefore we expect a 404 not found
        text = f'Lorem ipsum {workflow.REACTIE_ONTVANGEN} ...'
        endpoint = f'/signals/v1/private/signals/{self.signal.id}/email/preview/' \
                   f'?status={workflow.REACTIE_ONTVANGEN}&text={text}'

        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 404)

    def test_missing_required_query_parameter(self):
        # The status query parameter is required
        endpoint = f'/signals/v1/private/signals/{self.signal.id}/email/preview/'
        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 400)

    def test_not_authenticated(self):
        self.client.logout()

        endpoint = f'/signals/v1/private/signals/{self.signal.id}/email/preview/'
        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 401)

        self.client.force_authenticate(user=self.sia_read_write_user)

    def test_no_object_permission(self):
        # The sia_read_user should not be able to access the signal and therefore also not the email preview
        self.client.logout()
        self.client.force_authenticate(user=self.sia_read_user)

        endpoint = f'/signals/v1/private/signals/{self.signal.id}/email/preview/'
        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 403)

        self.client.logout()
        self.client.force_authenticate(user=self.sia_read_write_user)
