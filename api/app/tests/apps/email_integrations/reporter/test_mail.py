import uuid
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
from signals.apps.signals.models import Note
from tests.apps.signals.factories import SignalFactory, StatusFactory


class TestMailActionTriggers(TestCase):
    def setUp(self):
        self.signal = SignalFactory.create()

    @mock.patch('signals.apps.email_integrations.reporter.mail_actions.MailActions')
    def test_triggered_on_create_initial(self, patched_actions):
        create_initial.send_robust(sender=self.__class__, signal_obj=self.signal)
        patched_actions.apply.called_once()

    @mock.patch('signals.apps.email_integrations.reporter.mail_actions.MailActions')
    def test_triggered_on_update_status(self, patched_actions):
        prev_status = self.signal.status
        new_status = StatusFactory.create(_signal=self.signal, state=workflow.BEHANDELING)
        self.signal.status = new_status
        self.signal.save()

        update_status.send_robust(sender=self.__class__,
                                  signal_obj=self.signal,
                                  status=new_status,
                                  prev_status=prev_status)


class TestMailRuleConditions(TestCase):

    @freeze_time('2018-10-10T10:00+00:00')
    def setUp(self):
        def get_email():
            return f'{uuid.uuid4()}@example.com'

        self.signal = SignalFactory.create(reporter__email=get_email())
        self.signal_no_email = SignalFactory.create(reporter__email='')
        self.parent_signal = SignalFactory.create(reporter__email=get_email())
        self.child_signal = SignalFactory.create(reporter__email=get_email(),
                                                 parent=self.parent_signal)

    def _get_mail_rules(self, action_names):
        """
        Get MailActions object instantiated with specific mail rules.
        """
        mail_rules = [r for r in SIGNAL_MAIL_RULES if r['name'] in set(action_names)]
        return MailActions(mail_rules=mail_rules)

    def _apply_mail_actions(self, action_names, signal):
        """
        Apply only specified mail rules. (allows better isolation of tests)
        """
        mail_rules = [r for r in SIGNAL_MAIL_RULES if r['name'] in set(action_names)]
        ma = MailActions(mail_rules=mail_rules)
        ma.apply(signal_id=signal.id)

    def _find_messages(self, signal):
        # We use the unique email adresses to correlate a signal in the tests
        # and the eventual email. This does not work for anonymous reporters,
        # so our tests there are less robust.
        return [msg for msg in mail.outbox if signal.reporter.email in msg.to]

    def test_never_send_mail_for_child_signal(self):
        ma = MailActions(mail_rules=SIGNAL_MAIL_RULES)

        actions = ma._get_actions(self.child_signal)
        self.assertEqual(len(actions), 0)

        ma.apply(signal_id=self.child_signal.id, send_mail=True)
        self.assertEqual(len(mail.outbox), 0)

        # we want no history entry when no email was sent:
        self.assertEqual(Note.objects.count(), 0)

    def test_no_email_for_anonymous_reporter(self):
        ma = MailActions(mail_rules=SIGNAL_MAIL_RULES)
        ma.apply(self.signal_no_email.id, send_mail=True)

        self.assertEqual(len(mail.outbox), 0)

        # we want no history entry when no email was sent
        self.assertEqual(Note.objects.count(), 0)

    def test_send_mail_reporter_created(self):
        # Is the intended rule activated?
        actions = self._get_mail_rules(['Send mail signal created'])._get_actions(self.signal)
        self.assertEqual(len(actions), 1)

        # Is it the only one that activates?
        ma = MailActions(mail_rules=SIGNAL_MAIL_RULES)
        activated = ma._get_actions(self.signal)
        self.assertEqual(set(actions), set(activated))

        # Check mail contents
        ma.apply(signal_id=self.signal.id)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Bedankt voor uw melding {self.signal.id}')
        self.assertEqual(mail.outbox[0].to, [self.signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIn('10 oktober 2018 12:00', mail.outbox[0].body)
        category = self.signal.category_assignment.category
        self.assertIn(category.handling_message, mail.outbox[0].body)
        self.assertIn(settings.ORGANIZATION_NAME, mail.outbox[0].body)

        # we want a history entry when a email was sent
        self.assertEqual(Note.objects.count(), 1)

    def test_send_mail_reporter_created_custom_handling_message(self):
        # Make sure a category's handling messages makes it to the reporter via
        # the mail generated on creation of a nuisance complaint.
        category = self.signal.category_assignment.category
        category.handling_message = 'This text should end up in the mail to the reporter'
        category.save()
        self.signal.refresh_from_db()

        MailActions(mail_rules=SIGNAL_MAIL_RULES).apply(signal_id=self.signal.id)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Bedankt voor uw melding {self.signal.id}')
        self.assertEqual(mail.outbox[0].to, [self.signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIn(settings.ORGANIZATION_NAME, mail.outbox[0].body)

        self.assertIn('10 oktober 2018 12:00', mail.outbox[0].body)
        self.assertIn(category.handling_message, mail.outbox[0].body)

        # we want a history entry when a email was sent
        self.assertEqual(Note.objects.count(), 1)

    def test_send_mail_reporter_created_only_once(self):
        signal = SignalFactory.create(reporter__email='foo@bar.com')

        status = StatusFactory.create(_signal=signal, state=workflow.BEHANDELING)
        signal.status = status
        signal.save()

        status = StatusFactory.create(_signal=signal, state=workflow.GEMELD)
        signal.status = status
        signal.save()

        MailActions().apply(signal_id=signal.id, send_mail=True)
        self.assertEqual(len(mail.outbox), 0)

        # we want no history entry when no email was sent
        self.assertEqual(Note.objects.count(), 0)

    def test_send_mail_reporter_status_changed_afgehandeld(self):
        # Prepare signal with status change from `BEHANDELING` to `AFGEHANDELD`.
        StatusFactory.create(_signal=self.signal, state=workflow.BEHANDELING)
        status = StatusFactory.create(_signal=self.signal, state=workflow.AFGEHANDELD)
        self.signal.status = status
        self.signal.save()

        # Is the intended rule activated?
        actions = self._get_mail_rules(['Send mail signal handled'])._get_actions(self.signal)
        self.assertEqual(len(actions), 1)

        # Is it the only one that activates?
        ma = MailActions(mail_rules=SIGNAL_MAIL_RULES)
        activated = ma._get_actions(self.signal)
        self.assertEqual(set(actions), set(activated))

        # Check mail contents
        ma.apply(signal_id=self.signal.id)
        self.assertEqual(1, Feedback.objects.count())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Meer over uw melding {self.signal.id}')
        self.assertEqual(mail.outbox[0].to, [self.signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIn(settings.ORGANIZATION_NAME, mail.outbox[0].body)

        # we want a history entry when a email was sent
        self.assertEqual(Note.objects.count(), 1)

    def test_send_no_mail_reporter_status_changed_afgehandeld_after_verzoek_tot_heropenen(self):
        # Prepare signal with status change from `VERZOEK_TOT_HEROPENEN` to `AFGEHANDELD`,
        # this should not lead to an email being sent.
        StatusFactory.create(_signal=self.signal, state=workflow.VERZOEK_TOT_HEROPENEN)
        status = StatusFactory.create(_signal=self.signal, state=workflow.AFGEHANDELD)
        self.signal.status = status
        self.signal.save()

        # no mail rule should activate
        ma = MailActions(mail_rules=SIGNAL_MAIL_RULES)
        activated = ma._get_actions(self.signal)
        self.assertEqual(len(activated), 0)

        # Check mail contents
        ma.apply(signal_id=self.signal.id)
        self.assertEqual(0, Feedback.objects.count())
        self.assertEqual(len(mail.outbox), 0)

        # we want no history entry when no email was sent
        self.assertEqual(Note.objects.count(), 0)

    def test_send_mail_reporter_status_changed_afgehandeld_no_status_afgehandeld(self):
        # Note: SignalFactory always creates a signal with GEMELD status.
        # TODO: test is redundant, remove
        status = StatusFactory.create(_signal=self.signal, state=workflow.BEHANDELING)
        self.signal.status = status
        self.signal.save()

        # no mail rule should activate
        ma = MailActions(mail_rules=SIGNAL_MAIL_RULES)
        activated = ma._get_actions(self.signal)
        self.assertEqual(len(activated), 0)

        # Check mail contents
        ma.apply(signal_id=self.signal.id)
        self.assertEqual(0, Feedback.objects.count())
        self.assertEqual(len(mail.outbox), 0)

        # we want no history entry when no email was sent
        self.assertEqual(Note.objects.count(), 0)

    def test_send_mail_reporter_status_changed_afgehandeld_no_email(self):
        # Prepare signal with status change to `AFGEHANDELD`.
        StatusFactory.create(_signal=self.signal_no_email, state=workflow.BEHANDELING)
        status = StatusFactory.create(_signal=self.signal_no_email, state=workflow.AFGEHANDELD)
        self.signal_no_email.status = status
        self.signal_no_email.save()

        self._apply_mail_actions(['Send mail signal handled'], self.signal_no_email)

        # no mail rule should activate
        actions = self._get_mail_rules(['Send mail signal handled'])._get_actions(self.signal_no_email)
        self.assertEqual(len(actions), 0)

        # Check mail contents
        ma = MailActions()
        ma.apply(signal_id=self.signal_no_email.id)
        self.assertEqual(0, Feedback.objects.count())
        self.assertEqual(len(mail.outbox), 0)

        # we want no history entry when no email was sent
        self.assertEqual(Note.objects.count(), 0)

    def test_send_mail_reporter_status_changed_afgehandeld_txt_and_html(self):
        # Prepare signal with status change from `BEHANDELING` to `AFGEHANDELD`.
        StatusFactory.create(_signal=self.signal, state=workflow.BEHANDELING)
        status = StatusFactory.create(_signal=self.signal, state=workflow.AFGEHANDELD)
        self.signal.status = status
        self.signal.save()

        # Is the intended rule activated?
        actions = self._get_mail_rules(['Send mail signal handled'])._get_actions(self.signal)
        self.assertEqual(len(actions), 1)

        # Is it the only one that activates?
        ma = MailActions(mail_rules=SIGNAL_MAIL_RULES)
        activated = ma._get_actions(self.signal)
        self.assertEqual(set(actions), set(activated))

        # Check mail contents
        ma.apply(signal_id=self.signal.id)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(1, Feedback.objects.count())
        feedback = Feedback.objects.get(_signal__id=self.signal.id)

        message = mail.outbox[0]
        self.assertEqual(message.subject, f'Meer over uw melding {self.signal.id}')
        self.assertEqual(message.to, [self.signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)

        positive_feedback_url, negative_feedback_url = get_feedback_urls(feedback)
        context = {'negative_feedback_url': negative_feedback_url,
                   'positive_feedback_url': positive_feedback_url,
                   'signal': self.signal,
                   'status': status,
                   'ORGANIZATION_NAME': settings.ORGANIZATION_NAME, }
        txt_message = loader.get_template('email/signal_status_changed_afgehandeld.txt').render(context)
        html_message = loader.get_template('email/signal_status_changed_afgehandeld.html').render(context)

        self.assertEqual(message.body, txt_message)

        content, mime_type = message.alternatives[0]
        self.assertEqual(mime_type, 'text/html')
        self.assertEqual(content, html_message)

        # we want a history entry when a email was sent
        self.assertEqual(Note.objects.count(), 1)

    def test_links_in_different_environments(self):
        """Test that generated feedback links contain the correct host."""
        # Prepare signal with status change to `AFGEHANDELD`.
        StatusFactory.create(_signal=self.signal, state=workflow.BEHANDELING)
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
                ma = MailActions()
                ma.apply(signal_id=self.signal.id)

                self.assertEqual(len(mail.outbox), 1)
                message = mail.outbox[0]
                self.assertIn(fe_location, message.body)
                self.assertIn(fe_location, message.alternatives[0][0])

        # we want a history entry when a email was sent
        self.assertEqual(Note.objects.count(), len(env_fe_mapping))

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
                ma = MailActions()
                ma.apply(signal_id=self.signal.id)

                self.assertEqual(len(mail.outbox), 1)
                message = mail.outbox[0]
                self.assertIn('http://dummy_link', message.body)
                self.assertIn('http://dummy_link', message.alternatives[0][0])

        # we want a history entry when a email was sent
        self.assertEqual(Note.objects.count(), len(env_fe_mapping))


class TestOptionalMails(TestCase):
    @freeze_time('2018-10-10T10:00+00:00')
    def setUp(self):
        def get_email():
            return f'{uuid.uuid4()}@example.com'

        self.signal = SignalFactory.create(reporter__email=get_email())
        self.signal_no_email = SignalFactory.create(reporter__email='')
        self.parent_signal = SignalFactory.create(reporter__email=get_email())
        self.child_signal = SignalFactory.create(reporter__email=get_email(),
                                                 parent=self.parent_signal)

    def _get_mail_rules(self, action_names):
        """
        Get MailActions object instantiated with specific mail rules.
        """
        mail_rules = [r for r in SIGNAL_MAIL_RULES if r['name'] in set(action_names)]
        return MailActions(mail_rules=mail_rules)

    def test_optional_mail_GEMELD(self):
        # check normal signal
        new_status = StatusFactory.create(_signal=self.signal, state=workflow.GEMELD, send_email=False)
        self.signal.status = new_status
        self.signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.signal)
        self.assertEqual(len(rules), 0)

        new_status = StatusFactory.create(_signal=self.signal, state=workflow.GEMELD, send_email=True)
        self.signal.status = new_status
        self.signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.signal)
        self.assertEqual(len(rules), 1)

        # ... not for child signal
        new_status = StatusFactory.create(_signal=self.child_signal, state=workflow.GEMELD, send_email=True)
        self.child_signal.status = new_status
        self.child_signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.child_signal)
        self.assertEqual(len(rules), 0)

        # TODO: equivalent for parent signal cannot be tested yet (as it can
        # only have status.state=workflow.GESPLITST).

    @mock.patch('signals.apps.email_integrations.reporter.mail_actions.django_send_mail')
    def test_send_optional_mail_GEMELD(self, patched_send_mail):
        signal = self.signal
        new_status = StatusFactory.create(_signal=signal, state=workflow.GEMELD, send_email=True)
        signal.status = new_status
        signal.save()

        self._get_mail_rules(['Send mail optional']).apply(signal_id=signal.pk, send_mail=True)
        patched_send_mail.assert_called_once()
        self.assertEqual(Note.objects.count(), 1)

    def test_optional_mail_AFWACHTING(self):
        # check normal signal
        new_status = StatusFactory.create(_signal=self.signal, state=workflow.AFWACHTING, send_email=False)
        self.signal.status = new_status
        self.signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.signal)
        self.assertEqual(len(rules), 0)

        new_status = StatusFactory.create(_signal=self.signal, state=workflow.AFWACHTING, send_email=True)
        self.signal.status = new_status
        self.signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.signal)
        self.assertEqual(len(rules), 1)

        # ... not for child signal
        new_status = StatusFactory.create(_signal=self.child_signal, state=workflow.AFWACHTING, send_email=True)
        self.child_signal.status = new_status
        self.child_signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.child_signal)
        self.assertEqual(len(rules), 0)

    @mock.patch('signals.apps.email_integrations.reporter.mail_actions.django_send_mail')
    def test_send_optional_mail_AFWACHTING(self, patched_send_mail):
        signal = self.signal
        new_status = StatusFactory.create(_signal=signal, state=workflow.AFWACHTING, send_email=True)
        signal.status = new_status
        signal.save()

        self._get_mail_rules(['Send mail optional']).apply(signal_id=signal.pk, send_mail=True)
        patched_send_mail.assert_called_once()
        self.assertEqual(Note.objects.count(), 1)

    def test_optional_mail_BEHANDELING(self):
        # check normal signal
        new_status = StatusFactory.create(_signal=self.signal, state=workflow.BEHANDELING, send_email=False)
        self.signal.status = new_status
        self.signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.signal)
        self.assertEqual(len(rules), 0)

        new_status = StatusFactory.create(_signal=self.signal, state=workflow.BEHANDELING, send_email=True)
        self.signal.status = new_status
        self.signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.signal)
        self.assertEqual(len(rules), 1)

        # ... not for child signal
        new_status = StatusFactory.create(_signal=self.child_signal, state=workflow.BEHANDELING, send_email=True)
        self.child_signal.status = new_status
        self.child_signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.child_signal)
        self.assertEqual(len(rules), 0)

    @mock.patch('signals.apps.email_integrations.reporter.mail_actions.django_send_mail')
    def test_send_optional_mail_BEHANDELING(self, patched_send_mail):
        signal = self.signal
        new_status = StatusFactory.create(_signal=signal, state=workflow.BEHANDELING, send_email=True)
        signal.status = new_status
        signal.save()

        self._get_mail_rules(['Send mail optional']).apply(signal_id=signal.pk, send_mail=True)
        patched_send_mail.assert_called_once()
        self.assertEqual(Note.objects.count(), 1)

    def test_optional_mail_ON_HOLD(self):
        # check normal signal
        new_status = StatusFactory.create(_signal=self.signal, state=workflow.ON_HOLD, send_email=False)
        self.signal.status = new_status
        self.signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.signal)
        self.assertEqual(len(rules), 0)

        new_status = StatusFactory.create(_signal=self.signal, state=workflow.ON_HOLD, send_email=True)
        self.signal.status = new_status
        self.signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.signal)
        self.assertEqual(len(rules), 1)

        # ... not for child signal
        new_status = StatusFactory.create(_signal=self.child_signal, state=workflow.ON_HOLD, send_email=True)
        self.child_signal.status = new_status
        self.child_signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.child_signal)
        self.assertEqual(len(rules), 0)

    @mock.patch('signals.apps.email_integrations.reporter.mail_actions.django_send_mail')
    def test_send_optional_mail_ON_HOLD(self, patched_send_mail):
        signal = self.signal
        new_status = StatusFactory.create(_signal=signal, state=workflow.ON_HOLD, send_email=True)
        signal.status = new_status
        signal.save()

        self._get_mail_rules(['Send mail optional']).apply(signal_id=signal.pk, send_mail=True)
        patched_send_mail.assert_called_once()
        self.assertEqual(Note.objects.count(), 1)

    def test_optional_mail_VERZOEK_TOT_AFHANDELING(self):
        # check normal signal
        new_status = StatusFactory.create(_signal=self.signal, state=workflow.VERZOEK_TOT_AFHANDELING, send_email=False)
        self.signal.status = new_status
        self.signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.signal)
        self.assertEqual(len(rules), 0)

        new_status = StatusFactory.create(_signal=self.signal, state=workflow.VERZOEK_TOT_AFHANDELING, send_email=True)
        self.signal.status = new_status
        self.signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.signal)
        self.assertEqual(len(rules), 1)

        # ... not for child signal
        new_status = StatusFactory.create(
            _signal=self.child_signal, state=workflow.VERZOEK_TOT_AFHANDELING, send_email=True)
        self.child_signal.status = new_status
        self.child_signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.child_signal)
        self.assertEqual(len(rules), 0)

    @mock.patch('signals.apps.email_integrations.reporter.mail_actions.django_send_mail')
    def test_send_optional_mail_VERZOEK_TOT_AFHANDELING(self, patched_send_mail):
        signal = self.signal
        new_status = StatusFactory.create(_signal=signal, state=workflow.VERZOEK_TOT_AFHANDELING, send_email=True)
        signal.status = new_status
        signal.save()

        self._get_mail_rules(['Send mail optional']).apply(signal_id=signal.pk, send_mail=True)
        patched_send_mail.assert_called_once()
        self.assertEqual(Note.objects.count(), 1)

    def test_optional_mail_GEANNULEERD(self):
        # check normal signal
        new_status = StatusFactory.create(_signal=self.signal, state=workflow.GEANNULEERD, send_email=False)
        self.signal.status = new_status
        self.signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.signal)
        self.assertEqual(len(rules), 0)

        new_status = StatusFactory.create(_signal=self.signal, state=workflow.GEANNULEERD, send_email=True)
        self.signal.status = new_status
        self.signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.signal)
        self.assertEqual(len(rules), 1)

        # ... not for child signal
        new_status = StatusFactory.create(_signal=self.child_signal, state=workflow.GEANNULEERD, send_email=True)
        self.child_signal.status = new_status
        self.child_signal.save()

        rules = self._get_mail_rules(['Send mail optional'])._get_actions(self.child_signal)
        self.assertEqual(len(rules), 0)

    @mock.patch('signals.apps.email_integrations.reporter.mail_actions.django_send_mail')
    def test_send_optional_mail_GEANNULEERD(self, patched_send_mail):
        signal = self.signal
        new_status = StatusFactory.create(_signal=signal, state=workflow.GEANNULEERD, send_email=True)
        signal.status = new_status
        signal.save()

        self._get_mail_rules(['Send mail optional']).apply(signal_id=signal.pk, send_mail=True)
        patched_send_mail.assert_called_once()
        self.assertEqual(Note.objects.count(), 1)
