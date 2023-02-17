# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import datetime

from django.contrib.auth.models import Permission
from django.utils import timezone
from freezegun import freeze_time

from signals.apps.signals import workflow
from signals.apps.signals.factories import (
    CategoryFactory,
    ServiceLevelObjectiveFactory,
    SignalFactory
)
from signals.test.utils import SIAReadUserMixin, SignalsBaseApiTestCase


class TestPrivateSignalEndpointStatsTotal(SIAReadUserMixin, SignalsBaseApiTestCase):
    BASE_URI = '/signals/v1/private/signals/stats/total'

    def setUp(self):
        self.sia_read_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_user)

    def test_total_unfiltered(self):
        SignalFactory.create_batch(1000)

        response = self.client.get(self.BASE_URI)

        self.assertEqual(200, response.status_code)
        self.assertEqual(1000, response.json()['total'])

    def test_total_filtered_by_category(self):
        category1 = CategoryFactory.create()
        category2 = CategoryFactory.create()
        SignalFactory.create_batch(100, category_assignment__category=category1)
        SignalFactory.create_batch(100, category_assignment__category=category2)

        category_id = category1.pk
        response = self.client.get(self.BASE_URI + f'?category_id={category_id}')

        self.assertEqual(200, response.status_code)
        self.assertEqual(100, response.json()['total'])

    def test_total_filtered_by_priority(self):
        SignalFactory.create_batch(100, priority__priority='low')
        SignalFactory.create_batch(100, priority__priority='normal')
        SignalFactory.create_batch(100, priority__priority='high')

        response = self.client.get(self.BASE_URI + '?priority=normal')

        self.assertEqual(200, response.status_code)
        self.assertEqual(100, response.json()['total'])

    def test_total_filtered_by_punctuality(self):
        category = CategoryFactory.create()
        ServiceLevelObjectiveFactory.create(n_days=1, use_calendar_days=False, category=category)

        created_at = datetime.datetime(2023, 2, 1, 12, 0, 0, tzinfo=timezone.get_default_timezone())
        with freeze_time(created_at):
            SignalFactory.create_batch(100, category_assignment__category=category)

        def assert_punc(punc, **kwargs):
            with freeze_time(created_at + datetime.timedelta(**kwargs)):
                response = self.client.get(self.BASE_URI + f'?punctuality={punc}')

                self.assertEqual(200, response.status_code)
                self.assertEqual(100, response.json()['total'])

        assert_punc('on_time', seconds=60)
        assert_punc('late', days=2)
        assert_punc('late_factor_3', days=7)

    def test_total_filtered_by_area(self):
        SignalFactory.create_batch(100, location__stadsdeel='A')
        SignalFactory.create_batch(150, location__stadsdeel='E')

        response = self.client.get(self.BASE_URI + '?stadsdeel=A')

        self.assertEqual(200, response.status_code)
        self.assertEqual(100, response.json()['total'])


class TestPrivateSignalEndPointStatsPastWeek(SIAReadUserMixin, SignalsBaseApiTestCase):
    BASE_URI = '/signals/v1/private/signals/stats/past_week'

    def setUp(self):
        self.sia_read_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_user)

        self.today = datetime.datetime.today()
        self._setup_expectations(self.today)

    def test_past_week_filtered_by_afgehandeld_status(self):
        def create_signals(created_at, amount, state):
            with freeze_time(created_at):
                SignalFactory.create_batch(amount, status__state=state)

        data = (
            (self.today, 10, workflow.AFGEHANDELD),
            (self.today - datetime.timedelta(7), 11, workflow.AFGEHANDELD),
            (self.today - datetime.timedelta(1), 10, workflow.AFGEHANDELD),
            (self.today - datetime.timedelta(8), 10, workflow.AFGEHANDELD),
            (self.today - datetime.timedelta(3), 10, workflow.AFGEHANDELD),
            (self.today - datetime.timedelta(10), 0, workflow.AFGEHANDELD),
            (self.today - datetime.timedelta(4), 0, workflow.AFGEHANDELD),
            (self.today - datetime.timedelta(11), 10, workflow.AFGEHANDELD),
            (self.today - datetime.timedelta(5), 11, workflow.AFGEHANDELD),
            (self.today - datetime.timedelta(12), 10, workflow.AFGEHANDELD),
            (self.today - datetime.timedelta(6), 10, workflow.AFGEHANDELD),
            (self.today - datetime.timedelta(13), 20, workflow.AFGEHANDELD),
            (self.today, 2, workflow.HEROPEND),
            (self.today - datetime.timedelta(7), 15, workflow.HEROPEND),
            (self.today - datetime.timedelta(1), 3, workflow.BEHANDELING),
            (self.today - datetime.timedelta(8), 11, workflow.GEMELD),
            (self.today - datetime.timedelta(2), 7, workflow.AFWACHTING),
            (self.today - datetime.timedelta(9), 5, workflow.DOORGEZET_NAAR_EXTERN),
            (self.today - datetime.timedelta(3), 9, workflow.INGEPLAND),
            (self.today - datetime.timedelta(10), 2, workflow.REACTIE_GEVRAAGD),
            (self.today - datetime.timedelta(4), 1, workflow.VERZOEK_TOT_HEROPENEN),
            (self.today - datetime.timedelta(11), 8, workflow.REACTIE_ONTVANGEN),
            (self.today - datetime.timedelta(5), 3, workflow.AFGEHANDELD_EXTERN),
            (self.today - datetime.timedelta(12), 6, workflow.GEANNULEERD),
            (self.today - datetime.timedelta(6), 2, workflow.GESPLITST),
            (self.today - datetime.timedelta(13), 4, workflow.ON_HOLD),
        )

        for signal_data in data:
            create_signals(signal_data[0], signal_data[1], signal_data[2])

        response = self.client.get(self.BASE_URI + f'?status={workflow.AFGEHANDELD}')
        self._assert_response(response)

    def test_past_week_filtered_by_afgehandeld_status_and_category(self):
        def create_signals(created_at, amount, state, category):
            with freeze_time(created_at):
                SignalFactory.create_batch(amount, status__state=state, category_assignment__category=category)

        category1 = CategoryFactory.create()
        category2 = CategoryFactory.create()

        data = (
            (self.today, 10, workflow.AFGEHANDELD, category1),
            (self.today - datetime.timedelta(7), 11, workflow.AFGEHANDELD, category1),
            (self.today - datetime.timedelta(1), 10, workflow.AFGEHANDELD, category1),
            (self.today - datetime.timedelta(8), 10, workflow.AFGEHANDELD, category1),
            (self.today - datetime.timedelta(3), 10, workflow.AFGEHANDELD, category1),
            (self.today - datetime.timedelta(10), 0, workflow.AFGEHANDELD, category1),
            (self.today - datetime.timedelta(4), 0, workflow.AFGEHANDELD, category1),
            (self.today - datetime.timedelta(11), 10, workflow.AFGEHANDELD, category1),
            (self.today - datetime.timedelta(5), 11, workflow.AFGEHANDELD, category1),
            (self.today - datetime.timedelta(12), 10, workflow.AFGEHANDELD, category1),
            (self.today - datetime.timedelta(6), 10, workflow.AFGEHANDELD, category1),
            (self.today - datetime.timedelta(13), 20, workflow.AFGEHANDELD, category1),
            (self.today, 2, workflow.HEROPEND, category2),
            (self.today - datetime.timedelta(7), 15, workflow.HEROPEND, category2),
            (self.today - datetime.timedelta(1), 3, workflow.BEHANDELING, category2),
            (self.today - datetime.timedelta(8), 11, workflow.GEMELD, category2),
            (self.today - datetime.timedelta(2), 7, workflow.AFWACHTING, category2),
            (self.today - datetime.timedelta(9), 5, workflow.DOORGEZET_NAAR_EXTERN, category2),
            (self.today - datetime.timedelta(3), 9, workflow.INGEPLAND, category2),
            (self.today - datetime.timedelta(10), 2, workflow.REACTIE_GEVRAAGD, category2),
            (self.today - datetime.timedelta(4), 1, workflow.VERZOEK_TOT_HEROPENEN, category2),
            (self.today - datetime.timedelta(11), 8, workflow.REACTIE_ONTVANGEN, category2),
            (self.today - datetime.timedelta(5), 3, workflow.AFGEHANDELD_EXTERN, category2),
            (self.today - datetime.timedelta(12), 6, workflow.GEANNULEERD, category2),
            (self.today - datetime.timedelta(6), 2, workflow.GESPLITST, category2),
            (self.today - datetime.timedelta(13), 4, workflow.ON_HOLD, category2),
        )

        for signal_data in data:
            create_signals(signal_data[0], signal_data[1], signal_data[2], signal_data[3])

        response = self.client.get(self.BASE_URI + f'?status={workflow.AFGEHANDELD}&category_id={category1.pk}')
        self._assert_response(response)

    def test_past_week_filtered_by_afgehandeld_status_and_priority(self):
        def create_signals(created_at, amount, state, priority):
            with freeze_time(created_at):
                SignalFactory.create_batch(amount, status__state=state, priority__priority=priority)

        data = (
            (self.today, 10, workflow.AFGEHANDELD, 'high'),
            (self.today - datetime.timedelta(7), 11, workflow.AFGEHANDELD, 'high'),
            (self.today - datetime.timedelta(1), 10, workflow.AFGEHANDELD, 'high'),
            (self.today - datetime.timedelta(8), 10, workflow.AFGEHANDELD, 'high'),
            (self.today - datetime.timedelta(3), 10, workflow.AFGEHANDELD, 'high'),
            (self.today - datetime.timedelta(10), 0, workflow.AFGEHANDELD, 'high'),
            (self.today - datetime.timedelta(4), 0, workflow.AFGEHANDELD, 'high'),
            (self.today - datetime.timedelta(11), 10, workflow.AFGEHANDELD, 'high'),
            (self.today - datetime.timedelta(5), 11, workflow.AFGEHANDELD, 'high'),
            (self.today - datetime.timedelta(12), 10, workflow.AFGEHANDELD, 'high'),
            (self.today - datetime.timedelta(6), 10, workflow.AFGEHANDELD, 'high'),
            (self.today - datetime.timedelta(13), 20, workflow.AFGEHANDELD, 'high'),
            (self.today, 2, workflow.HEROPEND, 'low'),
            (self.today - datetime.timedelta(7), 15, workflow.HEROPEND, 'low'),
            (self.today - datetime.timedelta(1), 3, workflow.BEHANDELING, 'low'),
            (self.today - datetime.timedelta(8), 11, workflow.GEMELD, 'low'),
            (self.today - datetime.timedelta(2), 7, workflow.AFWACHTING, 'low'),
            (self.today - datetime.timedelta(9), 5, workflow.DOORGEZET_NAAR_EXTERN, 'low'),
            (self.today - datetime.timedelta(3), 9, workflow.INGEPLAND, 'low'),
            (self.today - datetime.timedelta(10), 2, workflow.REACTIE_GEVRAAGD, 'normal'),
            (self.today - datetime.timedelta(4), 1, workflow.VERZOEK_TOT_HEROPENEN, 'normal'),
            (self.today - datetime.timedelta(11), 8, workflow.REACTIE_ONTVANGEN, 'normal'),
            (self.today - datetime.timedelta(5), 3, workflow.AFGEHANDELD_EXTERN, 'normal'),
            (self.today - datetime.timedelta(12), 6, workflow.GEANNULEERD, 'normal'),
            (self.today - datetime.timedelta(6), 2, workflow.GESPLITST, 'normal'),
            (self.today - datetime.timedelta(13), 4, workflow.ON_HOLD, 'normal'),
        )

        for signal_data in data:
            create_signals(signal_data[0], signal_data[1], signal_data[2], signal_data[3])

        response = self.client.get(self.BASE_URI + f'?status={workflow.AFGEHANDELD}&priority=high')
        self._assert_response(response)

    def test_past_week_filtered_by_afgehandeld_status_and_area(self):
        def create_signals(created_at, amount, state, stadsdeel):
            with freeze_time(created_at):
                SignalFactory.create_batch(amount, status__state=state, location__stadsdeel=stadsdeel)

        data = (
            (self.today, 10, workflow.AFGEHANDELD, 'A'),
            (self.today - datetime.timedelta(7), 11, workflow.AFGEHANDELD, 'A'),
            (self.today - datetime.timedelta(1), 10, workflow.AFGEHANDELD, 'A'),
            (self.today - datetime.timedelta(8), 10, workflow.AFGEHANDELD, 'A'),
            (self.today - datetime.timedelta(3), 10, workflow.AFGEHANDELD, 'A'),
            (self.today - datetime.timedelta(10), 0, workflow.AFGEHANDELD, 'A'),
            (self.today - datetime.timedelta(4), 0, workflow.AFGEHANDELD, 'A'),
            (self.today - datetime.timedelta(11), 10, workflow.AFGEHANDELD, 'A'),
            (self.today - datetime.timedelta(5), 11, workflow.AFGEHANDELD, 'A'),
            (self.today - datetime.timedelta(12), 10, workflow.AFGEHANDELD, 'A'),
            (self.today - datetime.timedelta(6), 10, workflow.AFGEHANDELD, 'A'),
            (self.today - datetime.timedelta(13), 20, workflow.AFGEHANDELD, 'A'),
            (self.today, 2, workflow.HEROPEND, 'E'),
            (self.today - datetime.timedelta(7), 15, workflow.HEROPEND, 'E'),
            (self.today - datetime.timedelta(1), 3, workflow.BEHANDELING, 'E'),
            (self.today - datetime.timedelta(8), 11, workflow.GEMELD, 'E'),
            (self.today - datetime.timedelta(2), 7, workflow.AFWACHTING, 'E'),
            (self.today - datetime.timedelta(9), 5, workflow.DOORGEZET_NAAR_EXTERN, 'E'),
            (self.today - datetime.timedelta(3), 9, workflow.INGEPLAND, 'E'),
            (self.today - datetime.timedelta(10), 2, workflow.REACTIE_GEVRAAGD, 'E'),
            (self.today - datetime.timedelta(4), 1, workflow.VERZOEK_TOT_HEROPENEN, 'E'),
            (self.today - datetime.timedelta(11), 8, workflow.REACTIE_ONTVANGEN, 'E'),
            (self.today - datetime.timedelta(5), 3, workflow.AFGEHANDELD_EXTERN, 'E'),
            (self.today - datetime.timedelta(12), 6, workflow.GEANNULEERD, 'E'),
            (self.today - datetime.timedelta(6), 2, workflow.GESPLITST, 'E'),
            (self.today - datetime.timedelta(13), 4, workflow.ON_HOLD, 'E'),
        )

        for signal_data in data:
            create_signals(signal_data[0], signal_data[1], signal_data[2], signal_data[3])

        response = self.client.get(self.BASE_URI + f'?status={workflow.AFGEHANDELD}&stadsdeel=A')
        self._assert_response(response)

    def test_past_week_filtered_by_afgehandeld_status_and_punctuality(self):  # noqa: C901
        def create_signals(created_at, amount, state, category, delta, delta_3):
            with freeze_time(created_at):
                signals = SignalFactory.create_batch(
                    amount,
                    status__state=state,
                    category_assignment__category=category
                )

            for signal in signals:
                if delta is not None:
                    signal.category_assignment.deadline = signal.category_assignment.deadline - delta
                if delta_3 is not None:
                    signal.category_assignment.deadline_factor_3 = \
                        signal.category_assignment.deadline_factor_3 - delta_3
                signal.category_assignment.save(calculate_deadlines=False)

        slo_category = CategoryFactory.create()
        ServiceLevelObjectiveFactory.create(n_days=1, use_calendar_days=True, category=slo_category)

        today = datetime.datetime(2023, 2, 1, 12, 0, 0, tzinfo=timezone.get_default_timezone())

        data = (
            (today, 10, workflow.AFGEHANDELD, slo_category),
            (today - datetime.timedelta(7), 11, workflow.AFGEHANDELD, slo_category),
            (today - datetime.timedelta(1), 10, workflow.AFGEHANDELD, slo_category),
            (today - datetime.timedelta(8), 10, workflow.AFGEHANDELD, slo_category),
            (today - datetime.timedelta(3), 10, workflow.AFGEHANDELD, slo_category),
            (today - datetime.timedelta(10), 0, workflow.AFGEHANDELD, slo_category),
            (today - datetime.timedelta(4), 0, workflow.AFGEHANDELD, slo_category),
            (today - datetime.timedelta(11), 10, workflow.AFGEHANDELD, slo_category),
            (today - datetime.timedelta(5), 11, workflow.AFGEHANDELD, slo_category),
            (today - datetime.timedelta(12), 10, workflow.AFGEHANDELD, slo_category),
            (today - datetime.timedelta(6), 10, workflow.AFGEHANDELD, slo_category),
            (today - datetime.timedelta(13), 20, workflow.AFGEHANDELD, slo_category),
            (today, 2, workflow.HEROPEND, slo_category),
            (today - datetime.timedelta(7), 15, workflow.HEROPEND, slo_category),
            (today - datetime.timedelta(1), 3, workflow.BEHANDELING, slo_category),
            (today - datetime.timedelta(8), 11, workflow.GEMELD, slo_category),
            (today - datetime.timedelta(2), 7, workflow.AFWACHTING, slo_category),
            (today - datetime.timedelta(9), 5, workflow.DOORGEZET_NAAR_EXTERN, slo_category),
            (today - datetime.timedelta(3), 9, workflow.INGEPLAND, slo_category),
            (today - datetime.timedelta(10), 2, workflow.REACTIE_GEVRAAGD, slo_category),
            (today - datetime.timedelta(4), 1, workflow.VERZOEK_TOT_HEROPENEN, slo_category),
            (today - datetime.timedelta(11), 8, workflow.REACTIE_ONTVANGEN, slo_category),
            (today - datetime.timedelta(5), 3, workflow.AFGEHANDELD_EXTERN, slo_category),
            (today - datetime.timedelta(12), 6, workflow.GEANNULEERD, slo_category),
            (today - datetime.timedelta(6), 2, workflow.GESPLITST, slo_category),
            (today - datetime.timedelta(13), 4, workflow.ON_HOLD, slo_category),
        )

        time_deltas = (
            (datetime.timedelta(seconds=60), None),
            (datetime.timedelta(days=2), None),
            (datetime.timedelta(days=2), datetime.timedelta(days=21)),
        )
        for time_delta in time_deltas:
            for signal_data in data:
                create_signals(
                    signal_data[0],
                    signal_data[1],
                    signal_data[2],
                    signal_data[3],
                    time_delta[0],
                    time_delta[1],
                )

        punctuality_values = (
            'on_time',
            'late',
            'late_factor_3',
        )

        with freeze_time(today):
            i = 0
            for punctuality in punctuality_values:
                response = self.client.get(
                    self.BASE_URI + f'?status={workflow.AFGEHANDELD}&punctuality={punctuality}'
                )
                if i == 1:
                    self.expectations = (
                        {'date': (today - datetime.timedelta(6)).date(), 'amount': 20, 'amount_week_earlier': 40},
                        {'date': (today - datetime.timedelta(5)).date(), 'amount': 22, 'amount_week_earlier': 20},
                        {'date': (today - datetime.timedelta(4)).date(), 'amount': 0, 'amount_week_earlier': 20},
                        {'date': (today - datetime.timedelta(3)).date(), 'amount': 20, 'amount_week_earlier': 0},
                        {'date': (today - datetime.timedelta(2)).date(), 'amount': 0, 'amount_week_earlier': 0},
                        {'date': (today - datetime.timedelta(1)).date(), 'amount': 20, 'amount_week_earlier': 20},
                        {'date': today.date(), 'amount': 20, 'amount_week_earlier': 22},
                    )
                else:
                    self._setup_expectations(today)
                self._assert_response(response)
                i = i + 1

    def _setup_expectations(self, date):
        self.expectations = (
            {'date': (date - datetime.timedelta(6)).date(), 'amount': 10, 'amount_week_earlier': 20},
            {'date': (date - datetime.timedelta(5)).date(), 'amount': 11, 'amount_week_earlier': 10},
            {'date': (date - datetime.timedelta(4)).date(), 'amount': 0, 'amount_week_earlier': 10},
            {'date': (date - datetime.timedelta(3)).date(), 'amount': 10, 'amount_week_earlier': 0},
            {'date': (date - datetime.timedelta(2)).date(), 'amount': 0, 'amount_week_earlier': 0},
            {'date': (date - datetime.timedelta(1)).date(), 'amount': 10, 'amount_week_earlier': 10},
            {'date': date.date(), 'amount': 10, 'amount_week_earlier': 11},
        )

    def _assert_response(self, response):
        self.assertEqual(200, response.status_code)

        stats = response.json()
        self.assertEqual(len(self.expectations), len(stats))

        for i in range(len(stats)):
            self.assertEqual(self.expectations[i]['date'].isoformat(), stats[i]['date'])
            self.assertEqual(self.expectations[i]['amount'], stats[i]['amount'])
            self.assertEqual(self.expectations[i]['amount_week_earlier'], stats[i]['amount_week_earlier'])
