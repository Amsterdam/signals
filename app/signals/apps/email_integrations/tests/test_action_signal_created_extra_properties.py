# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.conf import settings
from django.core import mail
from django.test import TestCase

from signals.apps.email_integrations.actions import SignalCreatedAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models import Note


class TestSignalCreatedActionExtraProperties(TestCase):
    state = workflow.GEMELD
    action = SignalCreatedAction()

    def setUp(self):
        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_CREATED,
                                     title='Uw melding {{ formatted_signal_id }}'
                                           f' {EmailTemplate.SIGNAL_CREATED}',
                                     body='{% for label, answers in extra_properties.items %}{{ label }} {% for answer in answers %}{{ answer}}{% if not forloop.last %}, {% endif %}{% endfor %} {% endfor %}')  # noqa

    def test_signal_created_with_extra_properties(self):
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

    def test_signal_created_with_extra_properties_selected_objects_only_location(self):
        self.assertEqual(len(mail.outbox), 0)

        extra_properties = [
            {
                "id": "extra_straatverlichting_nummer",
                "label": "Lichtpunt(en) op kaart",
                "answer": {
                    "location": {
                        "address": {
                            "postcode": "1016EA",
                            "huisnummer": "237A",
                            "woonplaats": "Amsterdam",
                            "openbare_ruimte": "Keizersgracht"
                        },
                        "coordinates": {
                            "lat": 52.37223359027052,
                            "lng": 4.884936393337258
                        }
                    }
                },
                "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/lantaarnpaal-straatverlichting"  # noqa
            }
        ]

        signal = SignalFactory.create(status__state=self.state, reporter__email='test@example.com',
                                      extra_properties=extra_properties)

        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Uw melding {signal.get_id_display()} {self.action.key}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIn('Lichtpunt(en) op kaart', mail.outbox[0].body)
        self.assertIn('Locatie gepind op de kaart', mail.outbox[0].body)
        self.assertIn('Lichtpunt(en) op kaart Locatie gepind op de kaart', mail.outbox[0].body)

        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())
