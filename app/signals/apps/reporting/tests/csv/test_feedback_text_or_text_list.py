# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import csv
import os
import tempfile
from datetime import datetime
from unittest import mock

import pytz
from django.test import testcases

from signals.apps.feedback.factories import FeedbackFactory
from signals.apps.reporting.csv import datawarehouse
from signals.apps.signals.factories import SignalFactory


class TestFeedbackHandling(testcases.TestCase):
    """
    The KTO can have multiple answers selected since July 2022. However, the datawarehouse cannot process this list yet.
    Also, the frontend does not have the feature enabled to give multiple answers. Therefore, it was decided to return
    the text if set, if not set and there is a text_list use the first item of the text_list as the text. And still
    return the text_list in the CSV if present.
    """

    def setUp(self):
        self.csv_tmp_dir = tempfile.mkdtemp()

    @mock.patch.dict('os.environ', {'ENVIRONMENT': 'PRODUCTION'}, clear=True)
    def test_text_in_csv(self):
        signal = SignalFactory.create()
        feedback_submitted = FeedbackFactory.create(
            _signal=signal,
            created_at=datetime(2022, 10, 5, 12, 0, tzinfo=pytz.UTC),
            submitted_at=datetime(2022, 10, 5, 18, 0, 0, tzinfo=pytz.UTC),
            text='Zeer tevreden',
        )

        file_name = datawarehouse.create_kto_feedback_csv(self.csv_tmp_dir)
        self.assertEqual(os.path.split(file_name)[-1], 'kto-feedback-PRODUCTION.csv')

        # header and one entry should show up in written file.
        with open(file_name, 'r') as f:
            reader = csv.reader(f)

            self.assertEqual(len(list(reader)), 2)

            for row in reader:
                self.assertEqual(row['_signal_id'], str(feedback_submitted._signal.id))
                self.assertEqual(row['text'], feedback_submitted.text)
                self.assertEqual(row['text_list'], feedback_submitted.text_list)

    @mock.patch.dict('os.environ', {'ENVIRONMENT': 'PRODUCTION'}, clear=True)
    def test_text_and_text_list_in_csv(self):
        signal = SignalFactory.create()
        feedback_submitted = FeedbackFactory.create(
            _signal=signal,
            created_at=datetime(2022, 10, 5, 12, 0, tzinfo=pytz.UTC),
            submitted_at=datetime(2022, 10, 5, 18, 0, 0, tzinfo=pytz.UTC),
            text='Zeer tevreden',
            text_list=['Goed geholpen', 'Snel geholpen'],
        )

        file_name = datawarehouse.create_kto_feedback_csv(self.csv_tmp_dir)
        self.assertEqual(os.path.split(file_name)[-1], 'kto-feedback-PRODUCTION.csv')

        # header and one entry should show up in written file.
        with open(file_name, 'r') as f:
            reader = csv.reader(f)

            self.assertEqual(len(list(reader)), 2)

            for row in reader:
                self.assertEqual(row['_signal_id'], str(feedback_submitted._signal.id))
                self.assertEqual(row['text'], feedback_submitted.text)
                self.assertEqual(row['text_list'], feedback_submitted.text_list)

    @mock.patch.dict('os.environ', {'ENVIRONMENT': 'PRODUCTION'}, clear=True)
    def test_text_copied_first_item_from_text_list_in_csv(self):
        signal = SignalFactory.create()
        feedback_submitted = FeedbackFactory.create(
            _signal=signal,
            created_at=datetime(2022, 10, 5, 12, 0, tzinfo=pytz.UTC),
            submitted_at=datetime(2022, 10, 5, 18, 0, 0, tzinfo=pytz.UTC),
            text=None,
            text_list=['Goed geholpen', 'Snel geholpen'],
        )

        file_name = datawarehouse.create_kto_feedback_csv(self.csv_tmp_dir)
        self.assertEqual(os.path.split(file_name)[-1], 'kto-feedback-PRODUCTION.csv')

        # header and one entry should show up in written file.
        with open(file_name, 'r') as f:
            reader = csv.reader(f)

            self.assertEqual(len(list(reader)), 2)

            for row in reader:
                self.assertEqual(row['_signal_id'], str(feedback_submitted._signal.id))
                self.assertEqual(row['text'], feedback_submitted.text_list[0])
                self.assertEqual(row['text_list'], feedback_submitted.text_list)
