from unittest import mock

from django.conf import settings
from django.core import mail
from django.test import TestCase
from freezegun import freeze_time

from signals.apps.email_integrations.reporter import mail as reporter_mail
from signals.apps.feedback import app_settings as feedback_settings
from signals.apps.feedback.models import Feedback
from signals.apps.feedback.utils import get_feedback_urls
from signals.apps.signals import workflow
from tests.apps.signals.factories import SignalFactory, StatusFactory


class TestCore(TestCase):

    @freeze_time('2018-10-10T10:00+00:00')
    def setUp(self):
        self.signal = SignalFactory.create(reporter__email='foo@bar.com')
        self.signal_no_email = SignalFactory.create(reporter__email='')
        self.parent_signal = SignalFactory.create(reporter__email='foo@bar.com')
        self.child_signal = SignalFactory.create(reporter__email='foo@bar.com',
                                                 parent=self.parent_signal)

    def test_send_mail_reporter_created(self):
        category = self.signal.category_assignment.category
        num_of_messages = reporter_mail.send_mail_reporter_created(self.signal)

        self.assertEqual(num_of_messages, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Bedankt voor uw melding ({self.signal.id})')
        self.assertEqual(mail.outbox[0].to, ['foo@bar.com', ])

        self.assertIn('10 oktober 2018 12:00', mail.outbox[0].body)
        self.assertIn(category.handling_message, mail.outbox[0].body)

    def test_send_mail_reporter_created_custom_handling_message(self):
        category = self.signal.category_assignment.category
        category.handling_message = 'This text should end up in the mail to the reporter'
        category.save()
        self.signal.refresh_from_db()

        num_of_messages = reporter_mail.send_mail_reporter_created(self.signal)

        self.assertEqual(num_of_messages, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Bedankt voor uw melding ({self.signal.id})')
        self.assertEqual(mail.outbox[0].to, ['foo@bar.com', ])

        self.assertIn('10 oktober 2018 12:00', mail.outbox[0].body)
        self.assertIn(category.handling_message, mail.outbox[0].body)

    def test_send_mail_reporter_created_no_email(self):
        num_of_messages = reporter_mail.send_mail_reporter_created(self.signal_no_email)

        self.assertEqual(num_of_messages, None)

    def test_send_mail_reporter_status_changed_afgehandeld(self):
        # Prepare signal with status change from `BEHANDELING` to `AFGEHANDELD`.
        prev_status = StatusFactory.create(_signal=self.signal, state=workflow.BEHANDELING)
        status = StatusFactory.create(_signal=self.signal, state=workflow.AFGEHANDELD)
        self.signal.status = status
        self.signal.save()

        num_of_messages = reporter_mail.send_mail_reporter_status_changed_afgehandeld(
            self.signal, status, prev_status)

        self.assertEqual(1, Feedback.objects.count())
        self.assertEqual(num_of_messages, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Betreft melding: {self.signal.id}')
        self.assertEqual(mail.outbox[0].to, ['foo@bar.com', ])

    def test_send_no_mail_reporter_status_changed_afgehandeld_after_verzoek_tot_heropenen(self):
        # Prepare signal with status change from `VERZOEK_TOT_HEROPENEN` to `AFGEHANDELD`.
        prev_status = StatusFactory.create(
            _signal=self.signal, state=workflow.VERZOEK_TOT_HEROPENEN
        )
        status = StatusFactory.create(_signal=self.signal, state=workflow.AFGEHANDELD)
        self.signal.status = status
        self.signal.save()

        num_of_messages = reporter_mail.send_mail_reporter_status_changed_afgehandeld(
            self.signal, status, prev_status)

        self.assertEqual(0, Feedback.objects.count())
        self.assertEqual(num_of_messages, None)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_mail_reporter_status_changed_afgehandeld_no_status_afgehandeld(self):
        # Note: SignalFactory always creates a signal with GEMELD status.
        prev_status = self.signal.status
        status = StatusFactory.create(_signal=self.signal, state=workflow.BEHANDELING)
        self.signal.status = status
        self.signal.save()

        num_of_messages = reporter_mail.send_mail_reporter_status_changed_afgehandeld(
            signal=self.signal, status=self.signal.status, prev_status=prev_status
        )

        self.assertEqual(0, Feedback.objects.count())
        self.assertEqual(num_of_messages, None)

    def test_send_mail_reporter_status_changed_afgehandeld_no_email(self):
        # Prepare signal with status change to `AFGEHANDELD`.
        prev_status = StatusFactory.create(_signal=self.signal, state=workflow.BEHANDELING)
        status = StatusFactory.create(_signal=self.signal_no_email, state=workflow.AFGEHANDELD)
        self.signal_no_email.status = status
        self.signal_no_email.save()

        num_of_messages = reporter_mail.send_mail_reporter_status_changed_afgehandeld(
            self.signal_no_email, status, prev_status
        )

        self.assertEqual(0, Feedback.objects.count())
        self.assertEqual(num_of_messages, None)

    def test_send_mail_reporter_status_changed_afgehandeld_txt_and_html(self):
        mail.outbox = []

        # Prepare signal with status change from `BEHANDELING` to `AFGEHANDELD`.
        prev_status = StatusFactory.create(_signal=self.signal, state=workflow.BEHANDELING)
        status = StatusFactory.create(_signal=self.signal, state=workflow.AFGEHANDELD)
        self.signal.status = status
        self.signal.save()

        num_of_messages = reporter_mail.send_mail_reporter_status_changed_afgehandeld(
            self.signal, status, prev_status
        )

        self.assertEqual(1, Feedback.objects.count())
        feedback = Feedback.objects.get(_signal__id=self.signal.id)

        self.assertEqual(num_of_messages, 1)
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]

        self.assertEqual(message.subject, f'Betreft melding: {self.signal.id}')
        self.assertEqual(message.to, ['foo@bar.com', ])

        positive_feedback_url, negative_feedback_url = get_feedback_urls(feedback)
        context = {'negative_feedback_url': negative_feedback_url,
                   'positive_feedback_url': positive_feedback_url,
                   'signal': self.signal,
                   'status': status, }
        txt_message = reporter_mail._create_message('email/signal_status_changed_afgehandeld.txt',
                                                    context=context)
        html_message = reporter_mail._create_message('email/signal_status_changed_afgehandeld.html',
                                                     context=context)

        self.assertEqual(message.body, txt_message)

        content, mime_type = message.alternatives[0]
        self.assertEqual(mime_type, 'text/html')
        self.assertEqual(content, html_message)

    def test_links_in_different_environments(self):
        """Test that generated feedback links contain the correct host."""
        # Prepare signal with status change to `AFGEHANDELD`.
        prev_status = self.signal.status
        status = StatusFactory.create(_signal=self.signal, state=workflow.AFGEHANDELD)
        self.signal.status = status
        self.signal.save()

        # Check that generated emails contain the correct links for all
        # configured environments:
        env_fe_mapping = getattr(settings,
                                 'FEEDBACK_ENV_FE_MAPPING',
                                 feedback_settings.FEEDBACK_ENV_FE_MAPPING)
        self.assertEqual(len(env_fe_mapping), 3)  # sanity check Amsterdam installation has three

        for environment, fe_location in env_fe_mapping.items():
            local_env = {'ENVIRONMENT': environment}

            with mock.patch.dict('os.environ', local_env):
                mail.outbox = []
                num_of_messages = reporter_mail.send_mail_reporter_status_changed_afgehandeld(
                    self.signal, status, prev_status
                )

                self.assertEqual(num_of_messages, 1)
                self.assertEqual(len(mail.outbox), 1)
                message = mail.outbox[0]
                self.assertIn(fe_location, message.body)
                self.assertIn(fe_location, message.alternatives[0][0])

    def test_links_environment_env_var_not_set(self):
        """Deals with the case where nothing is overridden and `environment` not set."""
        # Prepare signal with status change to `AFGEHANDELD`.
        prev_status = self.signal.status
        status = StatusFactory.create(_signal=self.signal, state=workflow.AFGEHANDELD)
        self.signal.status = status
        self.signal.save()

        # Check that generated emails contain the correct links for all
        # configured environments:
        env_fe_mapping = feedback_settings.FEEDBACK_ENV_FE_MAPPING
        self.assertEqual(len(env_fe_mapping), 1)

        for environment, fe_location in env_fe_mapping.items():
            with mock.patch.dict('os.environ', {}, clear=True):
                mail.outbox = []
                num_of_messages = reporter_mail.send_mail_reporter_status_changed_afgehandeld(
                    self.signal, status, prev_status
                )

                self.assertEqual(num_of_messages, 1)
                self.assertEqual(len(mail.outbox), 1)
                message = mail.outbox[0]
                self.assertIn('http://dummy_link', message.body)
                self.assertIn('http://dummy_link', message.alternatives[0][0])


class TestSignalSplitEmailFlow(TestCase):
    def setUp(self):
        self.parent_signal = SignalFactory.create(
            status__state=workflow.GESPLITST, parent=None, reporter__email='piet@example.com')
        self.child_signal_1 = SignalFactory.create(
            status__state=workflow.GEMELD, parent=self.parent_signal)
        self.child_signal_2 = SignalFactory.create(
            status__state=workflow.GEMELD, parent=self.parent_signal)

    def test_send_mail_reporter_status_changed_split(self):
        """Original reporter must be emailed with resolution GESPLITST."""
        num_of_messages = reporter_mail.send_mail_reporter_status_changed_split(
            self.parent_signal, self.parent_signal.status)

        self.assertEqual(num_of_messages, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Betreft melding: {self.parent_signal.id}')
        self.assertEqual(mail.outbox[0].to, ['piet@example.com'])

    def test_send_mail_reporter_status_changed_split_no_correct_status(self):
        """No resolution GESPLITST email should be sent if status is not GESPLITST."""
        wrong_status = StatusFactory.create(state=workflow.GEMELD)
        self.parent_signal.status = wrong_status

        num_of_messages = reporter_mail.send_mail_reporter_status_changed_split(
            self.parent_signal, self.parent_signal.status)
        self.assertEqual(num_of_messages, None)

    def test_send_mail_reporter_status_changed_split_no_email(self):
        """No email should be sent when the reporter did not leave an email address."""
        self.parent_signal.reporter.email = None
        self.parent_signal.save()

        num_of_messages = reporter_mail.send_mail_reporter_status_changed_split(
            self.parent_signal, self.parent_signal.status)
        self.assertEqual(num_of_messages, None)
