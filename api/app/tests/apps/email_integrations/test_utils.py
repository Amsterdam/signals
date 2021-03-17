# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.conf import settings
from django.test import TestCase

from signals.apps.email_integrations.factories import EmailTemplateFactory
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.utils import (
    make_email_context,
    validate_email_template,
    validate_template
)
from signals.apps.signals.factories import SignalFactory


class TestUtils(TestCase):
    def test_make_email_context(self):
        signal = SignalFactory.create()
        context = make_email_context(signal=signal)

        self.assertEqual(context['signal_id'], signal.id)
        self.assertEqual(context['formatted_signal_id'], signal.sia_id)
        self.assertEqual(context['created_at'], signal.created_at)
        self.assertEqual(context['text'], signal.text)
        self.assertEqual(context['text_extra'], signal.text_extra)
        self.assertEqual(context['address'], signal.location.address)
        self.assertEqual(context['status_text'], signal.status.text)
        self.assertEqual(context['status_state'], signal.status.state)
        self.assertEqual(context['handling_message'], signal.category_assignment.stored_handling_message)
        self.assertEqual(context['ORGANIZATION_NAME'], settings.ORGANIZATION_NAME)

    def test_make_email_context_additional_context(self):
        signal = SignalFactory.create()
        context = make_email_context(signal=signal, additional_context={'extra': 'context'})

        self.assertEqual(context['signal_id'], signal.id)
        self.assertEqual(context['formatted_signal_id'], signal.sia_id)
        self.assertEqual(context['created_at'], signal.created_at)
        self.assertEqual(context['text'], signal.text)
        self.assertEqual(context['text_extra'], signal.text_extra)
        self.assertEqual(context['address'], signal.location.address)
        self.assertEqual(context['status_text'], signal.status.text)
        self.assertEqual(context['status_state'], signal.status.state)
        self.assertEqual(context['handling_message'], signal.category_assignment.stored_handling_message)
        self.assertEqual(context['ORGANIZATION_NAME'], settings.ORGANIZATION_NAME)
        self.assertEqual(context['extra'], 'context')

    def test_make_email_context_additional_context_should_not_override_default_variables(self):
        signal = SignalFactory.create()
        context = make_email_context(signal=signal, additional_context={'signal_id': 'test'})

        self.assertEqual(context['signal_id'], signal.id)
        self.assertNotEqual(context['signal_id'], 'test')

    def test_make_email_context_backwards_compatibility(self):
        """
        TODO: should be removed a.s.a.p.
        """
        signal = SignalFactory.create()
        context = make_email_context(signal=signal)

        self.assertEqual(context['signal'].id, signal.id)
        self.assertEqual(context['status']._signal_id, signal.id)
        self.assertEqual(context['status'].state, signal.status.state)

    def test_validate_email_template(self):
        email_template_valid = EmailTemplateFactory.create(key=EmailTemplate.SIGNAL_CREATED)
        result = validate_email_template(email_template_valid)
        self.assertTrue(result)

        email_template_invalid = EmailTemplateFactory.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD,
                                                             title='{{ text|lower:"a" }}',  # TemplateSyntaxError
                                                             body='{{ created_at|date:"B" }}')  # NotImplementedError
        result = validate_email_template(email_template_invalid)
        self.assertFalse(result)

        email_template_invalid_title = EmailTemplateFactory.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_HEROPEND,
                                                                   title='{{ created_at|date:"B" }}')  # noqa NotImplementedError
        result = validate_email_template(email_template_invalid_title)
        self.assertFalse(result)

        email_template_invalid_body = EmailTemplateFactory.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_OPTIONAL,
                                                                  body='{{ created_at|date:"B" }}')  # noqa NotImplementedError
        result = validate_email_template(email_template_invalid_body)
        self.assertFalse(result)

    def test_validate_template(self):
        self.assertTrue(validate_template('{{ text|lower }}'))
        self.assertFalse(validate_template('{{ text|lower:"a" }}'))  # TemplateSyntaxError
