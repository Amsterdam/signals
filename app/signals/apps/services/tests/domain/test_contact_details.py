# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import markdown
from django.test import TestCase

from signals.apps.email_integrations.markdown.plaintext import strip_markdown_html
from signals.apps.services.domain.contact_details import ContactDetailsService


class TestContactDetailsService(TestCase):
    email_cases = [
        ('test@test.com', 't**t@***t.com'),
        ('test.user@gmail.com', 't*******r@****l.com'),
        ('test.user@amsterdam.nl', 't*******r@********m.nl'),
        ('test@tst.com', 't**t@***.com'),
        ('tt@tst.com', 'tt@***.com'),
    ]
    phone_cases = [
        ('+31 6 12 34 56 78', '*******678'),
        ('+31612345678', '*******678'),
        ('06 12 34 56 78', '*******678'),
        ('0612345678', '*******678'),
    ]

    def test_obscure_email(self):
        for email, obscured_email in self.email_cases:
            self.assertEqual(ContactDetailsService.obscure_email(email, False), obscured_email)

    def test_obscure_email_for_markdown(self):
        for email, obscured_email in self.email_cases:
            encoded = ContactDetailsService.obscure_email(email, True)

            self.assertEqual(
                strip_markdown_html(markdown.markdown(encoded)),
                obscured_email
            )

    def test_obscure_phone(self):
        for phone, obscured_phone in self.phone_cases:
            self.assertEqual(ContactDetailsService.obscure_phone(phone, False), obscured_phone)

    def test_obscure_phone_for_markdown(self):
        for phone, obscured_phone in self.phone_cases:
            encoded = ContactDetailsService.obscure_phone(phone, True)

            self.assertEqual(
                strip_markdown_html(markdown.markdown(encoded)),
                obscured_phone
            )
