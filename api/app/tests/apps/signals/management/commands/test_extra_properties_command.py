# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from io import StringIO

from django.core.management import call_command
from django.test import TransactionTestCase

from signals.apps.signals.factories import SignalFactory


class TestExtraPropertiesCommand(TransactionTestCase):
    def test_command(self):
        invalid_extra_properties = [
            {
                "id": "wonen_overig",
                "label": "Wat is dit?",
                "answer": {
                    "id": "dit_is_een_test",
                    "info": "",
                    "label": "Dit is een test"
                },
                "category_url": ""
            }
        ]
        signal = SignalFactory.create(extra_properties=invalid_extra_properties)

        out = StringIO()
        err = StringIO()

        call_command('extra_properties', stdout=out, stderr=err)

        signal.refresh_from_db()
        self.assertNotEqual(signal.extra_properties[0]['category_url'], '')
        self.assertEqual(signal.extra_properties[0]['category_url'],
                         '/signals/v1/public/terms/categories/wonen/sub_categories/wonen-overig')

    def test_command_dry_run(self):
        invalid_extra_properties = [
            {
                "id": "wonen_overig",
                "label": "Wat is dit?",
                "answer": {
                    "id": "dit_is_een_test",
                    "info": "",
                    "label": "Dit is een test"
                },
                "category_url": ""
            }
        ]
        signal = SignalFactory.create(extra_properties=invalid_extra_properties)

        out = StringIO()
        err = StringIO()

        call_command('extra_properties', dry_run=True, stdout=out, stderr=err)

        signal.refresh_from_db()
        self.assertEqual(signal.extra_properties[0]['category_url'], '')
        self.assertNotEqual(signal.extra_properties[0]['category_url'],
                            '/signals/v1/public/terms/categories/wonen/sub_categories/wonen-overig')

    def test_command_signal_id(self):
        invalid_extra_properties = [
            {
                "id": "wonen_overig",
                "label": "Wat is dit?",
                "answer": {
                    "id": "dit_is_een_test",
                    "info": "",
                    "label": "Dit is een test"
                },
                "category_url": ""
            }
        ]
        signal = SignalFactory.create(extra_properties=invalid_extra_properties)
        signal_not_to_be_fixed = SignalFactory.create(extra_properties=invalid_extra_properties)

        out = StringIO()
        err = StringIO()

        call_command('extra_properties', signal_id=signal.id, stdout=out, stderr=err)

        signal.refresh_from_db()
        self.assertNotEqual(signal.extra_properties[0]['category_url'], '')
        self.assertEqual(signal.extra_properties[0]['category_url'],
                         '/signals/v1/public/terms/categories/wonen/sub_categories/wonen-overig')

        signal_not_to_be_fixed.refresh_from_db()
        self.assertEqual(signal_not_to_be_fixed.extra_properties[0]['category_url'], '')
        self.assertNotEqual(signal_not_to_be_fixed.extra_properties[0]['category_url'],
                            '/signals/v1/public/terms/categories/wonen/sub_categories/wonen-overig')
