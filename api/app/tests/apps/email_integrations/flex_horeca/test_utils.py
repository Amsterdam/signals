from django.test import TestCase
from freezegun import freeze_time

from signals.apps.email_integrations.flex_horeca import utils
from tests.apps.signals.factories import SignalFactory


class TestUtils(TestCase):
    signal = None
    signal_other_category = None

    def setUp(self):
        self.signal = SignalFactory.create(
            category_assignment__category__parent__name='Overlast Bedrijven en Horeca',
            category_assignment__category__name='Geluidsoverlast muziek'
        )

        self.signal_other_category = SignalFactory.create(
            category_assignment__category__parent__name='Some other main category',
            category_assignment__category__name='Some other category'
        )

    @freeze_time('2018-08-03')  # Friday
    def test_is_signal_applicable_in_category_on_friday(self):
        result = utils.is_signal_applicable(self.signal)
        self.assertEqual(result, True)

    @freeze_time('2018-08-05 01:00:00')  # Sunday 01:00
    def test_is_signal_applicable_in_category_on_sunday_before_end_time(self):
        result = utils.is_signal_applicable(self.signal)
        self.assertEqual(result, True)

    @freeze_time('2018-08-05 05:00:00')  # Sunday 05:00
    def test_is_signal_applicable_in_category_on_sunday_after_end_time(self):
        result = utils.is_signal_applicable(self.signal)
        self.assertEqual(result, False)

    @freeze_time('2018-08-03')  # Friday
    def test_is_signal_applicable_outside_category_on_friday(self):
        result = utils.is_signal_applicable(self.signal_other_category)
        self.assertEqual(result, False)
