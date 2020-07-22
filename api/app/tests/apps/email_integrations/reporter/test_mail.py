from unittest import mock

from django.conf import settings
from django.core import mail
from django.template import loader
from django.test import TestCase
from freezegun import freeze_time

from signals.apps.email_integrations.reporter.mail_actions import SIGNAL_MAIL_RULES, MailActions
from signals.apps.feedback import app_settings as feedback_settings
from signals.apps.feedback.models import Feedback
from signals.apps.feedback.utils import get_feedback_urls
from signals.apps.signals import workflow
from signals.apps.signals.managers import create_initial, update_status
from tests.apps.signals.factories import SignalFactory, StatusFactory


class TestCore(TestCase):
    ALL_RULE_NAMES = set([r['name'] for r in SIGNAL_MAIL_RULES])

    @freeze_time('2018-10-10T10:00+00:00')
    def setUp(self):
        self.signal = SignalFactory.create(reporter__email='foo@bar.com')
        self.signal_no_email = SignalFactory.create(reporter__email='')
        self.parent_signal = SignalFactory.create(reporter__email='foo@bar.com')
        self.child_signal = SignalFactory.create(reporter__email='foo@bar.com',
                                                 parent=self.parent_signal)

    def _apply_mail_actions(self, action_names, signal):
        """
        Apply only specified mail rules. (allows better isolation of tests)
        """
        mail_rules = [r for r in SIGNAL_MAIL_RULES if r['name'] in set(action_names)]
        ma = MailActions(mail_rules=mail_rules)

        return ma.apply(signal.id, send_mail=True)

    def test_send_mail_reporter_created(self):
        # Make sure an email is sent on creation of a nuisance complaint.
        category = self.signal.category_assignment.category
        self._apply_mail_actions(['Send mail signal created'], self.signal)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Bedankt voor uw melding ({self.signal.id})')
        self.assertEqual(mail.outbox[0].to, ['foo@bar.com', ])

        self.assertIn('10 oktober 2018 12:00', mail.outbox[0].body)
        self.assertIn(category.handling_message, mail.outbox[0].body)

    def test_send_mail_reporter_created_custom_handling_message(self):
        # Make sure a category's handling messages makes it to the reporter via
        # the mail generated on creation of a nuisance complaint.
        category = self.signal.category_assignment.category
        category.handling_message = 'This text should end up in the mail to the reporter'
        category.save()
        self.signal.refresh_from_db()

        self._apply_mail_actions(['Send mail signal created'], self.signal)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Bedankt voor uw melding ({self.signal.id})')
        self.assertEqual(mail.outbox[0].to, ['foo@bar.com', ])

        self.assertIn('10 oktober 2018 12:00', mail.outbox[0].body)
        self.assertIn(category.handling_message, mail.outbox[0].body)

    def test_send_mail_reporter_created_no_email(self):
        ma = MailActions(mail_rules=SIGNAL_MAIL_RULES)
        ma.apply(self.signal_no_email.id, send_mail=True)

        self.assertEqual(len(mail.outbox), 0)

    def test_send_mail_reporter_status_changed_afgehandeld(self):
        # Prepare signal with status change from `BEHANDELING` to `AFGEHANDELD`.
        StatusFactory.create(_signal=self.signal, state=workflow.BEHANDELING)
        status = StatusFactory.create(_signal=self.signal, state=workflow.AFGEHANDELD)
        self.signal.status = status
        self.signal.save()

        self._apply_mail_actions(['Send mail signal handled'], self.signal)

        self.assertEqual(1, Feedback.objects.count())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Betreft melding: {self.signal.id}')
        self.assertEqual(mail.outbox[0].to, ['foo@bar.com', ])

    def test_send_no_mail_reporter_status_changed_afgehandeld_after_verzoek_tot_heropenen(self):
        # Prepare signal with status change from `VERZOEK_TOT_HEROPENEN` to `AFGEHANDELD`,
        # this should not lead to an email being sent.
        StatusFactory.create(_signal=self.signal, state=workflow.VERZOEK_TOT_HEROPENEN)
        status = StatusFactory.create(_signal=self.signal, state=workflow.AFGEHANDELD)
        self.signal.status = status
        self.signal.save()

        self._apply_mail_actions(['Send mail signal handled'], self.signal)

        self.assertEqual(0, Feedback.objects.count())
        self.assertEqual(len(mail.outbox), 0)

    def test_send_mail_reporter_status_changed_afgehandeld_no_status_afgehandeld(self):
        # Note: SignalFactory always creates a signal with GEMELD status.
        # TODO: test is redundant, remove
        status = StatusFactory.create(_signal=self.signal, state=workflow.BEHANDELING)
        self.signal.status = status
        self.signal.save()

        self._apply_mail_actions(['Send mail signal handled'], self.signal)

        self.assertEqual(0, Feedback.objects.count())
        self.assertEqual(len(mail.outbox), 0)

    def test_send_mail_reporter_status_changed_afgehandeld_no_email(self):
        # Prepare signal with status change to `AFGEHANDELD`.
        StatusFactory.create(_signal=self.signal_no_email, state=workflow.BEHANDELING)
        status = StatusFactory.create(_signal=self.signal_no_email, state=workflow.AFGEHANDELD)
        self.signal_no_email.status = status
        self.signal_no_email.save()

        self._apply_mail_actions(['Send mail signal handled'], self.signal_no_email)

        self.assertEqual(0, Feedback.objects.count())
        self.assertEqual(len(mail.outbox), 0)

    def test_send_mail_reporter_status_changed_afgehandeld_txt_and_html(self):
        mail.outbox = []

        # Prepare signal with status change from `BEHANDELING` to `AFGEHANDELD`.
        StatusFactory.create(_signal=self.signal, state=workflow.BEHANDELING)
        status = StatusFactory.create(_signal=self.signal, state=workflow.AFGEHANDELD)
        self.signal.status = status
        self.signal.save()

        self._apply_mail_actions(['Send mail signal handled'], self.signal)

        self.assertEqual(1, Feedback.objects.count())
        feedback = Feedback.objects.get(_signal__id=self.signal.id)

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]

        self.assertEqual(message.subject, f'Betreft melding: {self.signal.id}')
        self.assertEqual(message.to, ['foo@bar.com', ])

        positive_feedback_url, negative_feedback_url = get_feedback_urls(feedback)
        context = {'negative_feedback_url': negative_feedback_url,
                   'positive_feedback_url': positive_feedback_url,
                   'signal': self.signal,
                   'status': status, }
        txt_message = loader.get_template('email/signal_status_changed_afgehandeld.txt').render(context)
        html_message = loader.get_template('email/signal_status_changed_afgehandeld.html').render(context)

        self.assertEqual(message.body, txt_message)

        content, mime_type = message.alternatives[0]
        self.assertEqual(mime_type, 'text/html')
        self.assertEqual(content, html_message)

    def test_links_in_different_environments(self):
        """Test that generated feedback links contain the correct host."""
        # Prepare signal with status change to `AFGEHANDELD`.
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
                self._apply_mail_actions(['Send mail signal handled'], self.signal)

                self.assertEqual(len(mail.outbox), 1)
                message = mail.outbox[0]
                self.assertIn(fe_location, message.body)
                self.assertIn(fe_location, message.alternatives[0][0])

    def test_links_environment_env_var_not_set(self):
        """Deals with the case where nothing is overridden and `environment` not set."""

        # Prepare signal with status change to `AFGEHANDELD`.
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
                self._apply_mail_actions(['Send mail signal handled'], self.signal)

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

    def _apply_mail_actions(self, action_names, signal):
        """
        Apply only specified mail rules. (allows better isolation of tests)
        """
        mail_rules = [r for r in SIGNAL_MAIL_RULES if r['name'] in set(action_names)]
        ma = MailActions(mail_rules=mail_rules)

        return ma.apply(signal.id, send_mail=True)

    def test_send_mail_reporter_status_changed_split(self):
        """Original reporter must be emailed with resolution GESPLITST."""
        ma = MailActions()
        ma.apply(self.parent_signal.id, send_mail=True)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Betreft melding: {self.parent_signal.id}')
        self.assertEqual(mail.outbox[0].to, ['piet@example.com'])

    def test_send_mail_reporter_status_changed_split_no_correct_status(self):
        """No resolution GESPLITST email should be sent if status is not GESPLITST."""
        self.parent_signal.status.state = 'workflow.GEMELD'
        self.parent_signal.status.save()

        self._apply_mail_actions(['Send mail signal split'], self.parent_signal)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_mail_reporter_status_changed_split_no_email(self):
        """No email should be sent when the reporter did not leave an email address."""
        self.parent_signal.reporter.email = None
        self.parent_signal.reporter.save()

        self._apply_mail_actions(['Send mail signal split'], self.parent_signal)
        self.assertEqual(len(mail.outbox), 0)


class TestReporterMailRules(TestCase):
    def setUp(self):
        self.signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='k.lager@example.com')
        self.signal_no_email = SignalFactory.create(status__state=workflow.GEMELD, reporter__email=None)

    def _update_status(self, state):
        prev_status = self.signal.status
        new_status = StatusFactory.create(state=state, _signal=self.signal)
        self.signal.status = new_status
        self.signal.save()

        update_status.send_robust(sender=self.__class__,
                                  signal_obj=self.signal,
                                  status=new_status,
                                  prev_status=prev_status)
        return prev_status, new_status

    def test_no_email_means_no_sending(self):
        create_initial.send_robust(sender=self.__class__, signal_obj=self.signal_no_email)

        self.assertEqual(len(mail.outbox), 0)

    def test_send_mail_AFGEHANDELD(self):
        self._update_status(workflow.AFGEHANDELD)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, [self.signal.reporter.email])
        self.assertEqual(message.subject, f'Betreft melding: {self.signal.id}')

    def test_send_mail_GEMELD(self):
        create_initial.send_robust(sender=self.__class__, signal_obj=self.signal)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, [self.signal.reporter.email])
        self.assertEqual(message.subject, f'Bedankt voor uw melding ({self.signal.id})')

    def test_send_mail_HEROPEND(self):
        self._update_status(workflow.HEROPEND)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, [self.signal.reporter.email])
        self.assertEqual(message.subject, f'Betreft melding: {self.signal.id}')

    def test_send_mail_INGEPLAND(self):
        self._update_status(workflow.INGEPLAND)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, [self.signal.reporter.email])
        self.assertEqual(message.subject, f'Betreft melding: {self.signal.id}')

    def test_send_mail_GESPLIT(self):
        self._update_status(workflow.GESPLITST)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, [self.signal.reporter.email])
        self.assertEqual(message.subject, f'Betreft melding: {self.signal.id}')
