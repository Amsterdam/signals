# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
import uuid
from datetime import timedelta
from unittest import mock
from urllib.parse import quote

from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from factory.fuzzy import FuzzyText
from freezegun import freeze_time

from signals.apps.email_integrations.actions import (
    SignalCreatedAction,
    SignalForwardToExternalAction,
    SignalHandledAction,
    SignalHandledNegativeAction,
    SignalOptionalAction,
    SignalReactionRequestAction,
    SignalReactionRequestReceivedAction,
    SignalReopenedAction,
    SignalScheduledAction
)
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.services import MailService
from signals.apps.feedback.factories import FeedbackFactory
from signals.apps.questionnaires.models import Session
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory, StatusFactory
from signals.apps.signals.models import Note, Signal


class ActionTestMixin:
    send_email = False

    def setUp(self):
        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_CREATED,
                                     title='Uw melding {{ formatted_signal_id }}'
                                           f' {EmailTemplate.SIGNAL_CREATED}',
                                     body='{{ text }} {{ created_at }} {{ handling_message }} {{ ORGANIZATION_NAME }}')

        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD,
                                     title='Uw melding {{ formatted_signal_id }}'
                                           f' {EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD}',
                                     body='{{ text }} {{ created_at }} {{ positive_feedback_url }} '
                                          '{{ negative_feedback_url }}{{ ORGANIZATION_NAME }}')

        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_INGEPLAND,
                                     title='Uw melding {{ formatted_signal_id }}'
                                           f' {EmailTemplate.SIGNAL_STATUS_CHANGED_INGEPLAND}',
                                     body='{{ text }} {{ created_at }} {{ ORGANIZATION_NAME }}')

        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_HEROPEND,
                                     title='Uw melding {{ formatted_signal_id }}'
                                           f' {EmailTemplate.SIGNAL_STATUS_CHANGED_HEROPEND}',
                                     body='{{ text }} {{ created_at }} {{ ORGANIZATION_NAME }}')

        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_OPTIONAL,
                                     title='Uw melding {{ formatted_signal_id }}'
                                           f' {EmailTemplate.SIGNAL_STATUS_CHANGED_OPTIONAL}',
                                     body='{{ text }} {{ created_at }} {{ status_text }} {{ ORGANIZATION_NAME }}')

        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_GEVRAAGD,
                                     title='Uw melding {{ formatted_signal_id }}'
                                           f' {EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_GEVRAAGD}',
                                     body='{{ text }} {{ created_at }} {{ status_text }} {{ reaction_url }} '
                                          '{{ ORGANIZATION_NAME }}')

        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_ONTVANGEN,
                                     title='Uw melding {{ formatted_signal_id }}'
                                           f' {EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_ONTVANGEN}',
                                     body='{{ text }} {{ created_at }} {{ reaction_request_answer }} '
                                          '{{ ORGANIZATION_NAME }}')

        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD_KTO_NEGATIVE_CONTACT,
                                     title='Uw melding {{ formatted_signal_id }}'
                                           f' {EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD_KTO_NEGATIVE_CONTACT}',
                                     body='{{ text }} {{ created_at }} {{ reaction_request_answer }} '
                                          '{{ ORGANIZATION_NAME }} {{ feedback_text }} {{ feedback_text_extra }} ')

        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_FORWARD_TO_EXTERNAL,
                                     title='Uw melding {{ formatted_signal_id }}'
                                           f' {EmailTemplate.SIGNAL_STATUS_CHANGED_FORWARD_TO_EXTERNAL}',
                                     body='{{ text }} {{ reaction_url }}'
                                          '{{ ORGANIZATION_NAME }}')

    def test_send_email(self):
        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=400)
        signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                      status__send_email=self.send_email, reporter__email='test@example.com')
        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Uw melding {signal.get_id_display()} {self.action.key}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

    def test_send_email_dry_run(self):
        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=400)
        signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                      status__send_email=self.send_email, reporter__email='test@example.com')
        self.assertTrue(self.action(signal, dry_run=True))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Note.objects.count(), 0)
        self.assertFalse(Note.objects.filter(text=self.action.note).exists())

    def test_send_email_anonymous(self):
        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=400)
        signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                      status__send_email=self.send_email, reporter__email='')
        self.assertFalse(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Note.objects.count(), 0)
        self.assertFalse(Note.objects.filter(text=self.action.note).exists())

        signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                      status__send_email=self.send_email, reporter__email=None)
        self.assertFalse(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Note.objects.count(), 0)
        self.assertFalse(Note.objects.filter(text=self.action.note).exists())

    def test_send_email_for_parent_signals(self):
        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=400)
        parent_signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                             status__send_email=self.send_email, reporter__email='test@example.com')
        SignalFactory.create(status__state=self.state, status__text=status_text, reporter__email='test@example.com',
                             parent=parent_signal)
        self.assertTrue(self.action(parent_signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

    def test_do_not_send_email_for_child_signals(self):
        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=400)
        parent_signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                             status__send_email=self.send_email, reporter__email='test@example.com')
        child_signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                            status__send_email=self.send_email, reporter__email='test@example.com',
                                            parent=parent_signal)
        self.assertFalse(self.action(child_signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Note.objects.count(), 0)
        self.assertFalse(Note.objects.filter(text=self.action.note).exists())

    def test_do_not_send_email_invalid_states(self):
        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=400)
        states = list(map(lambda x: x[0] and x[0] == self.state, workflow.STATUS_CHOICES))
        for state in states:
            signal = SignalFactory.create(status__state=state, status__text=status_text,
                                          status__send_email=True, reporter__email='test@example.com')
            self.assertFalse(self.action(signal))
            self.assertEqual(Note.objects.count(), 0)
            self.assertFalse(Note.objects.filter(text=self.action.note).exists())

    @mock.patch('signals.apps.email_integrations.actions.abstract.send_mail', autospec=True)
    def test_send_email_fails(self, mocked):
        mocked.return_value = False

        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=400)
        signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                      status__send_email=True, reporter__email='test@example.com')
        self.assertFalse(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)

    def test_allowed_contact_false(self):
        """
        Disable all emails when a signal has a feedback object with allows_contact False
        """
        status_text = FuzzyText(length=400)
        signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                      status__send_email=self.send_email, reporter__email='test@example.com')
        feedback = FeedbackFactory.create(
            _signal=signal,
            allows_contact=False,
            submitted_at='2022-01-01 00:00:00+00:00'
        )
        feedback.save()
        signal.save()
        self.assertFalse(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(FEATURE_FLAGS={
        'REPORTER_MAIL_CONTACT_FEEDBACK_ALLOWS_CONTACT_ENABLED': False,
    })
    def test_allowed_contact_disable_flag(self):
        """
        When the flag is set to false the feature should always return true and still mail the users
        """
        status_text = FuzzyText(length=400)
        signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                      status__send_email=self.send_email, reporter__email='test@example.com')
        feedback = FeedbackFactory.create(
            _signal=signal,
            allows_contact=False,
            submitted_at='2022-01-01 00:00:00+00:00'
        )
        feedback.save()
        signal.save()
        self.assertTrue(self.action(signal, dry_run=False))
        self.assertTrue(len(mail.outbox) > 0)

    def test_send_mail_fails_encoded_chars_in_text(self):
        """
        The action should not send an email if the text contains encoded characters. A note should be added so that
        it is clear why the email was not sent. This is also logged in Sentry and/or Application Insights.
        """
        self.assertEqual(len(mail.outbox), 0)

        unquoted_url = 'https://user:password@test-domain.com/?query=param&extra=param'
        quoted_url = unquoted_url
        # Let's encode the URL 10 times
        for _ in range(10):
            quoted_url = quote(quoted_url)

        signal_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut ' \
                      f'labore et dolore magna aliqua. {quoted_url} Ut enim ad minim veniam, quis nostrud ' \
                      'exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.'

        status_text = FuzzyText(length=200)

        signal = SignalFactory.create(text=signal_text, text_extra=signal_text, status__state=self.state,
                                      status__text=status_text, status__send_email=True,
                                      reporter__email='test@example.com')
        self.assertFalse(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)

        signal.refresh_from_db()
        self.assertEqual(signal.notes.count(), 1)
        self.assertEqual(signal.notes.first().text,
                         'E-mail is niet verzonden omdat er verdachte tekens in de meldtekst staan.')


class TestSignalCreatedAction(ActionTestMixin, TestCase):
    """
    Test the SignalCreatedAction. The action should only be triggerd when the following rules apply:

    - The status is GEMELD
    - The status GEMELD is set only once
    """
    state = workflow.GEMELD
    action = SignalCreatedAction()

    def test_signal_set_state_second_time(self):
        """
        Check that if the status GEMELD is set for a second time the action is not triggered
        """
        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=self.state, reporter__email='test@example.com')

        status = StatusFactory.create(_signal=signal, state=workflow.BEHANDELING)
        signal.status = status
        signal.save()

        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        self.assertFalse(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Note.objects.count(), 0)
        self.assertFalse(Note.objects.filter(text=self.action.note).exists())

    def test_signal_set_state_multiple_times(self):
        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=self.state, reporter__email='test@example.com')

        for x in range(5):
            with freeze_time(timezone.now() + timedelta(hours=x)):
                status = StatusFactory.create(_signal=signal, state=self.state)
                signal.status = status
                signal.save()

        self.assertFalse(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Note.objects.count(), 0)
        self.assertFalse(Note.objects.filter(text=self.action.note).exists())

    def test_signal_created_with_reporter_email(self):
        email_template = EmailTemplate.objects.get(key=EmailTemplate.SIGNAL_CREATED)
        email_template.body = '{% if reporter_email %} {{ reporter_email }} {% endif %}'
        email_template.save()

        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=self.state, reporter__email='test@example.com')

        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Uw melding {signal.get_id_display()} {self.action.key}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIn('t**t@******e.com', mail.outbox[0].body)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

    def test_signal_created_with_reporter_email_small_tld(self):
        email_template = EmailTemplate.objects.get(key=EmailTemplate.SIGNAL_CREATED)
        email_template.body = '{% if reporter_email %} {{ reporter_email }} {% endif %}'
        email_template.save()

        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=self.state, reporter__email='tt@tt.com')

        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Uw melding {signal.get_id_display()} {self.action.key}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIn('tt@**.com', mail.outbox[0].body)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

    def test_signal_created_with_reporter_email_and_phone(self):
        email_template = EmailTemplate.objects.get(key=EmailTemplate.SIGNAL_CREATED)
        email_template.body = '{% if reporter_email %} {{ reporter_email }} {% endif %} ' \
                              '{% if reporter_phone %} {{ reporter_phone }} {% endif %}'
        email_template.save()

        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=self.state, reporter__email='test@example.com',
                                      reporter__phone='0612345678')

        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Uw melding {signal.get_id_display()} {self.action.key}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)

        self.assertIn('t**t@******e.com', mail.outbox[0].body)
        self.assertIn('*******678', mail.outbox[0].body)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

    def test_signal_created_sharing_allowed_reporter(self):
        """
        Test the sharing allowed if it is enabled
        """
        email_template = EmailTemplate.objects.get(key=EmailTemplate.SIGNAL_CREATED)
        email_template.body = '{% if reporter_sharing_allowed %} is allowed {% else %} not allowed {% endif %}'
        email_template.save()

        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=self.state, reporter__email='test@example.com',
                                      reporter__sharing_allowed=True)

        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Uw melding {signal.get_id_display()} {self.action.key}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)

        self.assertIn('is allowed', mail.outbox[0].body)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

    def test_signal_created_sharing_NOT_allowed_reporter(self):
        """
        Test the sharing allowed if it is enabled
        """
        email_template = EmailTemplate.objects.get(key=EmailTemplate.SIGNAL_CREATED)
        email_template.body = '{% if reporter_sharing_allowed %} is allowed {% else %} not allowed {% endif %}'
        email_template.save()

        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=self.state, reporter__email='test@example.com',
                                      reporter__sharing_allowed=False)

        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Uw melding {signal.get_id_display()} {self.action.key}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)

        self.assertIn('not allowed', mail.outbox[0].body)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

    def test_signal_created_with_extra_properties(self):
        email_template = EmailTemplate.objects.get(key=EmailTemplate.SIGNAL_CREATED)
        email_template.body = '{% for label, answers in extra_properties.items %}{{ label }} {% for answer in answers %}{{ answer}}{% if not forloop.last %}, {% endif %}{% endfor %} {% endfor %}'  # noqa
        email_template.save()

        self.assertEqual(len(mail.outbox), 0)

        extra_properties = [
            {
                "id": "test-1",
                "label": "Is dit de eerste vraag?",
                "answer": "Ja, en dit is het antwoord op de eerste vraag",
                "category_url": "/signals/v1/public/terms/categories/overig/sub_categories/overig"
            }, {
                "id": "test-2",
                "label": "Is dit de tweede vraag en selecteren wij hier een of meerdere objecten?",
                "answer": [{
                    "id": 12345,
                    "type": "type-1",
                    "description": "Overig lichtpunt",
                    "label": "Overig lichtpunt",
                }, {
                    "id": 67890,
                    "type": "not-on-map",
                    "label": "Lichtpunt niet op de kaart"
                }, {
                    "type": "not-on-map"
                }],
                "category_url": "/signals/v1/public/terms/categories/overig/sub_categories/overig"
            }, {
                "id": "extra_straatverlichting_probleem",
                "label": "Probleem",
                "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/lantaarnpaal-straatverlichting",  # noqa
                "answer": {
                    "id": "lamp_doet_het_niet",
                    "label": "Lamp doet het niet",
                    "info": ""
                }
            },
            {
                "id": "extra_straatverlichting",
                "label": "Denkt u dat de situatie gevaarlijk is?",
                "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/lantaarnpaal-straatverlichting",  # noqa
                "answer": {
                    "id": "niet_gevaarlijk",
                    "label": "Nee, niet gevaarlijk",
                    "info": ""
                }
            },
            {
                "id": "extra_fietswrak",
                "label": "Extra informatie",
                "answer": "2 wrakken met hele oude gemeentelijke labels en 2 tegen een lantaarnpaal in het gras en nog een losse zwarte met zachte band",  # noqa
                "category_url": "/signals/v1/public/terms/categories/overlast-in-de-openbare-ruimte/sub_categories/fietswrak"  # noqa
            }
        ]

        signal = SignalFactory.create(status__state=self.state, reporter__email='test@example.com',
                                      extra_properties=extra_properties)

        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Uw melding {signal.get_id_display()} {self.action.key}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)

        self.assertIn('Is dit de eerste vraag?', mail.outbox[0].body)
        self.assertIn('Ja, en dit is het antwoord op de eerste vraag', mail.outbox[0].body)
        self.assertIn('Overig lichtpunt, Lichtpunt niet op de kaart, not-on-map', mail.outbox[0].body)
        self.assertIn('Probleem', mail.outbox[0].body)
        self.assertIn('Lamp doet het niet', mail.outbox[0].body)
        self.assertIn('Denkt u dat de situatie gevaarlijk is?', mail.outbox[0].body)
        self.assertIn('Nee, niet gevaarlijk', mail.outbox[0].body)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

    def test_signal_created_with_extra_properties_set_to_none(self):
        email_template = EmailTemplate.objects.get(key=EmailTemplate.SIGNAL_CREATED)
        email_template.body = '{% for label, answers in extra_properties.items %}{{ label }} {% for answer in answers %}{{ answer}}{% if not forloop.last %}, {% endif %}{% endfor %} {% endfor %}'  # noqa
        email_template.save()

        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=self.state, reporter__email='test@example.com',
                                      extra_properties=None)

        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Uw melding {signal.get_id_display()} {self.action.key}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)

        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())


class TestSignalHandledAction(ActionTestMixin, TestCase):
    """
    Test the SignalHandledAction. The action should only be triggerd when the following rules apply:

    - The status is AFGEHANDELD
    - The previous state is not VERZOEK_TOT_HEROPENEN
    """
    state = workflow.AFGEHANDELD
    action = SignalHandledAction()

    def test_signal_set_state_second_time(self):
        """
        If the Signal status is set to AFGEHANDELD a second time and the previous state is not VERZOEK_TOT_HEROPENEN
        the action should be triggered
        """
        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')

        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

        status = StatusFactory.create(_signal=signal, state=workflow.HEROPEND)
        signal.status = status
        signal.save()

        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(Note.objects.count(), 2)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

    def test_signal_set_state_second_time_second_last_state_verzoek_tot_heropenen(self):
        """
        If the Signal status is set to AFGEHANDELD a second time and the previous state is VERZOEK_TOT_HEROPENEN the
        action should not be triggered
        """
        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')

        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

        status = StatusFactory.create(_signal=signal, state=workflow.VERZOEK_TOT_HEROPENEN)
        signal.status = status
        signal.save()

        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        self.assertFalse(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())


class TestSignalHandledNegativeAction(ActionTestMixin, TestCase):
    action = SignalHandledNegativeAction()
    state = workflow.AFGEHANDELD
    prev_state = workflow.VERZOEK_TOT_HEROPENEN
    signal = None
    feedback = None

    def setUp(self):
        status_text = FuzzyText(length=400)
        self.signal = SignalFactory.create(status__state=self.prev_state, status__text=status_text,
                                           status__send_email=self.send_email, reporter__email='test@example.com')

        # create the new current state
        status = StatusFactory.create(_signal=self.signal, state=self.state)
        self.signal.status = status
        self.signal.save()
        self.feedback = FeedbackFactory.create(
            _signal=self.signal,
            allows_contact=True,
            is_satisfied=False
        )
        self.feedback.save()
        super().setUp()

    def test_send_email(self):
        self.assertEqual(len(mail.outbox), 0)
        self.assertTrue(self.action(self.signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Uw melding {self.signal.get_id_display()} {self.action.key}')
        self.assertEqual(mail.outbox[0].to, [self.signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

    def test_send_email_dry_run(self):
        self.assertEqual(len(mail.outbox), 0)

        self.assertTrue(self.action(self.signal, dry_run=True))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Note.objects.count(), 0)
        self.assertFalse(Note.objects.filter(text=self.action.note).exists())

    def test_send_email_for_parent_signals(self):
        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=400)
        parent_signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                             status__send_email=self.send_email, reporter__email='test@example.com')
        SignalFactory.create(status__state=self.state, status__text=status_text, reporter__email='test@example.com',
                             parent=self.signal)

        self.assertFalse(self.action(parent_signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Note.objects.count(), 0)

    @override_settings(FEATURE_FLAGS={
        'REPORTER_MAIL_CONTACT_FEEDBACK_ALLOWS_CONTACT_ENABLED': False,
    })
    def test_allowed_contact_disable_flag(self):
        """
        When the flag is set to false the feature should always return true and still mail the users
        """
        self.assertTrue(self.action(self.signal, dry_run=False))
        self.assertTrue(len(mail.outbox) > 0)

    def test_send_mail_fails_encoded_chars_in_text(self):
        """
        The action should not send an email if the text contains encoded characters. A note should be added so that
        it is clear why the email was not sent. This is also logged in Sentry and/or Application Insights.
        """
        self.assertEqual(len(mail.outbox), 0)

        unquoted_url = 'https://user:password@test-domain.com/?query=param&extra=param'
        quoted_url = unquoted_url
        # Let's encode the URL 10 times
        for _ in range(10):
            quoted_url = quote(quoted_url)

        signal_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut ' \
                      f'labore et dolore magna aliqua. {quoted_url} Ut enim ad minim veniam, quis nostrud ' \
                      'exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.'

        self.signal.text_extra = signal_text
        self.signal.save()

        self.assertFalse(self.action(self.signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)

        self.signal.refresh_from_db()
        self.assertEqual(self.signal.notes.count(), 1)
        self.assertEqual(self.signal.notes.first().text,
                         'E-mail is niet verzonden omdat er verdachte tekens in de meldtekst staan.')

    @override_settings(FEATURE_FLAGS={
        'REPORTER_MAIL_HANDLED_NEGATIVE_CONTACT_ENABLED': False,
    })
    def test_feature_flag_disabled(self):
        self.assertFalse(self.action(self.signal, dry_run=False))

    def test_get_additional_context(self):
        self.feedback.text = 'ahoy'
        self.feedback.text_extra = 'ahoy extra'
        self.feedback.allows_contact = True
        self.feedback.is_satisfied = False
        self.feedback.save()
        context = self.action.get_additional_context(self.signal)

        self.assertIn('feedback_text', context)
        self.assertIn('feedback_text_extra', context)
        self.assertIn('feedback_allows_contact', context)
        self.assertIn('feedback_is_satisfied', context)
        self.assertEqual(context['feedback_text'], self.feedback.text)
        self.assertEqual(context['feedback_text_extra'], self.feedback.text_extra)
        self.assertEqual(context['feedback_allows_contact'], self.feedback.allows_contact)
        self.assertEqual(context['feedback_is_satisfied'], self.feedback.is_satisfied)

    def test_get_additional_context_no_feedback(self):

        signal = SignalFactory.create(status__state=self.state, status__text='some_text',
                                      status__send_email=self.send_email, reporter__email='test@example.com')
        context = self.action.get_additional_context(signal)
        self.assertFalse(any(context))

    def test_context_in_template(self):

        self.feedback.text = 'text_12345'
        self.feedback.text_extra = 'text_extra_9876'
        self.feedback.allows_contact = True
        self.feedback.is_satisfied = False
        self.feedback.save()

        self.assertTrue(self.action(self.signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        self.assertIn(self.feedback.text, body)
        self.assertIn(self.feedback.text_extra, body)


class TestSignalScheduledAction(ActionTestMixin, TestCase):
    """
    Test the SignalScheduledAction. The action should only be triggerd when the following rules apply:

    - The status is INGEPLAND
    - send_email must be True
    """
    state = workflow.INGEPLAND
    send_email = True
    action = SignalScheduledAction()


class TestSignalReopenedAction(ActionTestMixin, TestCase):
    """
    Test the SignalReopenedAction. The action should only be triggerd when the following rules apply:

    - The status is HEROPEND
    """
    state = workflow.HEROPEND
    action = SignalReopenedAction()


class TestSignalReactionRequestAction(ActionTestMixin, TestCase):
    """
    Test the SignalReactionRequestAction. The action should only be triggerd when the following rules apply:

    - The status is REACTIE_GEVRAAGD
    """
    state = workflow.REACTIE_GEVRAAGD
    action = SignalReactionRequestAction()

    def test_send_email(self):
        """
        Also check that the FRONTEND_URL is present in the message body
        """
        super().test_send_email()

        message = mail.outbox[0]
        self.assertIn(settings.FRONTEND_URL, message.body)
        self.assertIn(settings.FRONTEND_URL, message.alternatives[0][0])


class TestSignalReactionRequestReceivedAction(ActionTestMixin, TestCase):
    """
    Test the SignalReactionRequestReceivedAction. The action should only be triggerd when the following rules apply:

    - The status is REACTIE_ONTVANGEN
    - The status text does not match NO_REACTION_RECEIVED_TEXT
    """
    state = workflow.REACTIE_ONTVANGEN
    send_email = True
    action = SignalReactionRequestReceivedAction()

    def test_send_email(self):
        self.assertEqual(len(mail.outbox), 0)

        status_text = 'Aanvullend antwoord naar aanleiding van reactie gevraagd is gegeven.'
        signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                      status__send_email=self.send_email, reporter__email='test@example.com')
        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Uw melding {signal.get_id_display()} {self.action.key}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

        message = mail.outbox[0]
        self.assertIn(status_text, message.body)
        self.assertIn(status_text, message.alternatives[0][0])


class TestSignalOptionalAction(TestCase):
    """
    Test the SignalOptionalAction. The action should only be triggerd when the following rules apply:

    - The status is GEMELD, AFWACHTING, BEHANDELING, ON_HOLD, VERZOEK_TOT_AFHANDELING or GEANNULEERD
    - send_email must be True
    """
    action = SignalOptionalAction()

    def test_statuses(self):
        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')

        statuses = [
            workflow.GEMELD,
            workflow.AFWACHTING,
            workflow.BEHANDELING,
            workflow.ON_HOLD,
            workflow.VERZOEK_TOT_AFHANDELING,
            workflow.GEANNULEERD,
        ]

        for state in statuses:
            status = StatusFactory.create(_signal=signal, state=state, send_email=True)
            signal.status = status
            signal.save()

            self.assertTrue(self.action(signal, dry_run=False))

    def test_statuses_do_not_apply(self):
        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')

        statuses = [
            workflow.GEMELD,
            workflow.AFWACHTING,
            workflow.BEHANDELING,
            workflow.ON_HOLD,
            workflow.VERZOEK_TOT_AFHANDELING,
            workflow.GEANNULEERD,
        ]

        for state in statuses:
            status = StatusFactory.create(_signal=signal, state=state, send_email=False)
            signal.status = status
            signal.save()

            self.assertFalse(self.action(signal, dry_run=False))

    def test_statuses_not_allowed(self):
        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')

        statuses = [
            workflow.LEEG,
            workflow.AFGEHANDELD,
            workflow.GESPLITST,
            workflow.HEROPEND,
            workflow.INGEPLAND,
            workflow.VERZOEK_TOT_HEROPENEN,
            workflow.TE_VERZENDEN,
            workflow.VERZONDEN,
            workflow.VERZENDEN_MISLUKT,
            workflow.AFGEHANDELD_EXTERN,
        ]

        for state in statuses:
            status = StatusFactory.create(_signal=signal, state=state, send_email=True)
            signal.status = status
            signal.save()

            self.assertFalse(self.action(signal, dry_run=False))


class TestSignalForwardToExternalAction(ActionTestMixin, TestCase):
    state = workflow.DOORZETTEN_NAAR_EXTERN
    action = SignalForwardToExternalAction()
    send_email = True

    def test_send_email(self):
        self.assertEqual(EmailTemplate.objects.count(), 9)
        self.assertTrue(bool(EmailTemplate.SIGNAL_STATUS_CHANGED_FORWARD_TO_EXTERNAL))
        template = EmailTemplate.objects.get(key=EmailTemplate.SIGNAL_STATUS_CHANGED_FORWARD_TO_EXTERNAL)
        self.assertIsInstance(template, EmailTemplate)

        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=400)
        signal = SignalFactory.create(status__state=self.state,
                                      status__text=status_text,
                                      status__email_override='a@example.com',
                                      status__send_email=self.send_email,
                                      reporter__email='test@example.com')
        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Uw melding {signal.get_id_display()} {self.action.key}')
        self.assertEqual(mail.outbox[0].to, [signal.status.email_override, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

    def test_send_email_dry_run(self):
        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=400)
        signal = SignalFactory.create(status__state=self.state,
                                      status__text=status_text,
                                      status__email_override='a@example.com',
                                      status__send_email=self.send_email,
                                      reporter__email='test@example.com')
        self.assertTrue(self.action(signal, dry_run=True))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Note.objects.count(), 0)
        self.assertFalse(Note.objects.filter(text=self.action.note).exists())

    def test_send_email_for_parent_signals(self):
        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=400)
        parent_signal = SignalFactory.create(status__state=self.state,
                                             status__text=status_text,
                                             status__send_email=self.send_email,
                                             status__email_override='a@example.com',
                                             reporter__email='test@example.com')
        SignalFactory.create(status__state=self.state, status__text=status_text, reporter__email='test@example.com',
                             parent=parent_signal)
        self.assertTrue(self.action(parent_signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

    def test_allowed_contact_disable_flag(self):
        """
        Whether or not the reporter allows email is not relevant when emailing external collaborators.
        """
        template = EmailTemplate.objects.get(key=EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD)
        self.assertIsInstance(template, EmailTemplate)

        template = EmailTemplate.objects.get(key=EmailTemplate.SIGNAL_STATUS_CHANGED_FORWARD_TO_EXTERNAL)
        self.assertIsInstance(template, EmailTemplate)

        status_text = FuzzyText(length=400)
        signal = SignalFactory.create(status__state=self.state,
                                      status__text=status_text,
                                      status__email_override='a@example.com',
                                      status__send_email=self.send_email,
                                      reporter__email='test@example.com')
        feedback = FeedbackFactory.create(
            _signal=signal,
            allows_contact=False,
            submitted_at='2022-01-01 00:00:00+00:00'
        )
        feedback.save()
        signal.save()
        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        # TODO add check that external collaborator received an email

    def test_send_mail_fails_encoded_chars_in_text(self):
        """
        The action should not send an email if the text contains encoded characters. A note should be added so that
        it is clear why the email was not sent. This is also logged in Sentry and/or Application Insights.
        """
        self.assertEqual(len(mail.outbox), 0)

        unquoted_url = 'https://user:password@test-domain.com/?query=param&extra=param'
        quoted_url = unquoted_url
        # Let's encode the URL 10 times
        for _ in range(10):
            quoted_url = quote(quoted_url)

        signal_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut ' \
                      f'labore et dolore magna aliqua. {quoted_url} Ut enim ad minim veniam, quis nostrud ' \
                      'exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.'

        status_text = FuzzyText(length=200)

        signal = SignalFactory.create(text=signal_text, text_extra=signal_text, status__state=self.state,
                                      status__email_override='a@example.com',
                                      status__text=status_text, status__send_email=True,
                                      reporter__email='test@example.com')
        self.assertFalse(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)

        signal.refresh_from_db()
        self.assertEqual(signal.notes.count(), 1)
        self.assertEqual(signal.notes.first().text,
                         'E-mail is niet verzonden omdat er verdachte tekens in de meldtekst staan.')

    def test_get_additional_context(self):
        self.assertEqual(Session.objects.count(), 0)
        status_text = FuzzyText(length=400)

        signal = SignalFactory.create(status__state=workflow.DOORZETTEN_NAAR_EXTERN, status__send_email=True,
                                      status__email_override='a@example.com', status__text=status_text)
        context = self.action.get_additional_context(signal)

        session = Session.objects.first()
        self.assertIn('reaction_url', context)
        self.assertEqual(context['reaction_url'], f'{settings.FRONTEND_URL}/incident/extern/{session.uuid}')


class TestSignalCreatedActionNoTemplate(TestCase):
    """
    Test the SignalOptionalAction. No EmailTemplate(s) are present in the database, therefor the fallback template
    should be used. The action should only be triggerd when the following rules apply:

    - The status is GEMELD
    - The status GEMELD is set only once
    """
    state = workflow.GEMELD
    action = SignalCreatedAction()

    def test_send_email(self):
        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=self.state, reporter__email='test@example.com')
        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Bedankt voor uw melding {signal.get_id_display()}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())


class TestSignalStatusActions(TestCase):

    def test_always_require_rule(self):
        """
        Verify that status actions always have a rule attached
        """
        for action in MailService._status_actions:
            self.assertIsNotNone(action.rule)


class TestAbstractSystemAction(TestCase):

    def test_call_invalid_kwargs(self):
        action = MailService._system_actions.get('feedback_received')()
        self.assertRaises(TypeError, action, signal='fake_test_signal')


class TestSignalSystemActions(TestCase):

    def setUp(self) -> None:
        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_FEEDBACK_RECEIVED,
                                     title='Uw feedback is ontvangen',
                                     body='{{ feedback_text }} {{ feedback_text_extra }} '
                                          '{{ feedback_allows_contact }} {{ feedback_is_satisfied }}')
        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_FORWARD_TO_EXTERNAL_REACTION_RECEIVED,
                                     title='Uw reactie is ontvangen',
                                     body='{{ reaction_text }} {{ signal_id }} {{ created_at }} {{ address }}')

    def test_system_action_rule(self):
        """
        Mail actions from the _system_actions in MailService dont have a rule and always return True
        """
        for key, action in MailService._system_actions.items():
            self.assertTrue(action().rule('fake_signal'))

    def test_send_system_email_with_context(self):
        """
        Check if the email with context is send to the user
        """
        action = MailService._system_actions.get('feedback_received')()
        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')

        text = 'my text _1234567'
        text_extra = 'my extra text _extra_987654321'
        feedback = FeedbackFactory.create(
            _signal=signal,
            text=text,
            text_extra=text_extra,
            token=uuid.uuid4()
        )
        result = action(signal=signal, dry_run=False, feedback=feedback)
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIn(text, mail.outbox[0].body)
        self.assertIn(text_extra, mail.outbox[0].body)
        self.assertEqual(Note.objects.count(), 1)

    def test_send_system_email_dry_run(self):
        action = MailService._system_actions.get('feedback_received')()
        signal = SignalFactory()
        feedback = FeedbackFactory.create(
            token=uuid.uuid4(), _signal=signal)
        self.assertTrue(action(signal=signal, dry_run=True, feedback=feedback))

    def test_feedback_received_action_context(self):
        text = 'my text'
        text_extra = 'my extra text'
        signal = SignalFactory()
        feedback = FeedbackFactory.create(
            text=text,
            text_extra=text_extra,
            allows_contact=True,
            is_satisfied=False,
            token=uuid.uuid4(),
            _signal=signal
        )

        action = MailService._system_actions.get('feedback_received')()
        action(signal=signal, feedback=feedback)
        result = action.get_additional_context(signal)

        self.assertIn('feedback_text', result)
        self.assertIn('feedback_text_extra', result)
        self.assertIn('feedback_allows_contact', result)
        self.assertIn('feedback_is_satisfied', result)
        self.assertEqual(result['feedback_text'], text)
        self.assertEqual(result['feedback_text_extra'], text_extra)
        self.assertTrue(result['feedback_allows_contact'])
        self.assertFalse(result['feedback_is_satisfied'])

    @override_settings(FEATURE_FLAGS={'SYSTEM_MAIL_FEEDBACK_RECEIVED_ENABLED': False})
    def test_feedback_received_action_disabled(self):
        """
        FeedbackReceivedAction is disabled in settings
        """
        action = MailService._system_actions.get('feedback_received')()
        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')

        text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'
        text_extra = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'
        feedback = FeedbackFactory.create(_signal=signal, text=text, text_extra=text_extra, token=uuid.uuid4())

        result = action(signal=signal, dry_run=False, feedback=feedback)
        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)

    def test_forward_to_external_reaction_received_send_mail(self):
        action = MailService._system_actions.get('forward_to_external_reaction_received')()

        signal = SignalFactory.create(
            status__state=workflow.DOORZETTEN_NAAR_EXTERN,
            reporter__email='reporter@example.com',
            status__send_email=True,
            status__email_override='external@example.com')
        Signal.actions.update_status({'state': workflow.VERZOEK_TOT_AFHANDELING, 'text': 'please fix'}, signal)

        result = action(signal=signal, dry_run=False, reaction_text='fixed!', email_override='external@example.com')
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['external@example.com', ])

    def test_forward_to_external_reaction_received_context(self):
        action = MailService._system_actions.get('forward_to_external_reaction_received')()

        signal = SignalFactory.create(
            status__state=workflow.DOORZETTEN_NAAR_EXTERN,
            reporter__email='reporter@example.com',
            status__send_email=True,
            status__email_override='external@example.com')
        Signal.actions.update_status({'state': workflow.VERZOEK_TOT_AFHANDELING, 'text': 'please fix'}, signal)

        result = action(signal=signal, reaction_text='reaction text', email_override='external@example.com')
        self.assertTrue(result)
        context = action.get_additional_context(signal)
        self.assertIn('reaction_text', context)

        full_context = action.get_context(signal)
        self.assertIn('created_at', full_context)
        self.assertIn('address', full_context)
        self.assertIn('signal_id', full_context)
