from datetime import datetime, timedelta
from random import shuffle

from freezegun import freeze_time

from signals.apps.signals.workflow import BEHANDELING, GEMELD, ON_HOLD
from tests.apps.signals.factories import (
    CategoryAssignmentFactory,
    CategoryFactory,
    SignalFactory,
    StatusFactory
)
from tests.test import SignalsBaseApiTestCase


class TestFilters(SignalsBaseApiTestCase):
    """ Tests filters on the private v1 list endpoint: /signals/v1/private/signals """
    SIGNALS_DISTRIBUTE_DAYS_CNT = 10
    SIGNALS_DISTRIBUTE_HOURS_CNT = 10
    SUBCATEGORY_CNT = 5
    LIST_ENDPOINT = '/signals/v1/private/signals/'

    signals = []
    sub_categories = []
    states = []

    @classmethod
    def _create_signals(cls):
        """
        Creates SIGNALS_DISTRIBUTE_DAYS_CNT signals. One per day backwards starting from yesterday
        current time.
        Creates SIGNALS_DISTRIBUTE_HOURS_CNT signals every hour backwards from now

        If today is Friday 16:00, and SIGNALS_DISTRIBUTE_DAYS_CNT and SIGNALS_DISTRIBUTE_HOURS_CNT
        are both set to 3, we will generate the following signals:
        - Per day: Thursday (yesterday) 16:00, Wednesday (day before yesterday) 16:00, Tuesday 16:00
        - Per hour: Friday 16:00 (now), Friday 15:00 (now minus 1 hour), Friday 14:00 (now minus 2h)
        """
        now = datetime.utcnow()

        # Generate created/updated times for new signals.
        times = [now - timedelta(days=idx + 1)
                 for idx in range(cls.SIGNALS_DISTRIBUTE_DAYS_CNT)] + \
                [now - timedelta(hours=idx)
                 for idx in range(cls.SIGNALS_DISTRIBUTE_HOURS_CNT)]

        cls.states = 3 * [BEHANDELING] + 2 * [ON_HOLD] + (len(times) - 3 - 2) * [GEMELD]
        shuffle(cls.states)

        cls.sub_categories = [CategoryFactory.create() for _ in range(cls.SUBCATEGORY_CNT)]

        for idx, time in enumerate(times):
            with freeze_time(time):
                signal = SignalFactory.create()
                StatusFactory(_signal=signal, state=cls.states[idx])
                category_assignment = CategoryAssignmentFactory(_signal=signal,
                                                                category=cls.sub_categories[
                                                                    idx % len(cls.sub_categories)])
                signal.category_assignment = category_assignment
                signal.save()

                cls.signals.append(signal)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_signals()

    def setUp(self):
        self.signals = TestFilters.signals
        self.sub_categories = TestFilters.sub_categories
        self.states = TestFilters.states

    def _request_filter_signals(self, filter_params: dict):
        """ Does a filter request and returns the signal ID's present in the request """
        self.client.force_authenticate(user=self.superuser)
        resp = self.client.get(self.LIST_ENDPOINT, data=filter_params)

        self.assertEqual(200, resp.status_code)

        resp_json = resp.json()
        ids = [res["id"] for res in resp_json["results"]]

        self.assertEqual(resp_json["count"], len(ids))

        return ids

    def test_result_all(self):
        """ No filtering should return all """
        result_ids = self._request_filter_signals({})
        self.assertEqual(len(self.signals), len(result_ids))

    def test_filter_id(self):
        """ Filtering on id should return one signal """
        id = self.signals[0].id
        result_ids = self._request_filter_signals({"id": id})

        self.assertEqual(1, len(result_ids))
        self.assertListEqual([id], result_ids)

    def test_filter_updated_after(self):
        """ Test updated_after """
        now = datetime.now()

        params = {"updated_after": now - timedelta(hours=4, minutes=30)}
        result_ids = self._request_filter_signals(params)

        # Expect 5 results. now, now - 1, now - 2, now - 3, now - 4 hours
        self.assertEqual(5, len(result_ids))

    def test_filter_updated_before(self):
        """ Test updated_before """
        now = datetime.now()

        params = {"updated_before": now - timedelta(hours=18)}
        result_ids = self._request_filter_signals(params)

        # Expect 10 results
        self.assertEqual(10, len(result_ids))

    def test_filter_created_after(self):
        """ Test created_after """
        now = datetime.now()

        params = {"created_after": now - timedelta(minutes=30)}
        result_ids = self._request_filter_signals(params)

        self.assertEqual(1, len(result_ids))

    def test_filter_created_before(self):
        """ Test created_before """
        now = datetime.now()

        params = {"created_before": now - timedelta(days=8, hours=12)}
        result_ids = self._request_filter_signals(params)

        self.assertEqual(2, len(result_ids))

    def test_filter_combined_no_results(self):
        """ Test combination of created_before and created_after, distinct sets """
        some_point_in_time = datetime.now() - timedelta(hours=3)

        params = {
            # Should return nothing. Sets are distinct, so no results
            "created_before": some_point_in_time - timedelta(minutes=1),
            "created_after": some_point_in_time + timedelta(minutes=1),
        }

        result_ids = self._request_filter_signals(params)
        self.assertEqual(0, len(result_ids))

    def test_filter_combined_with_one_result(self):
        """ Test combination of created_before and created_after, union contains one signal """
        some_point_in_time = datetime.now() - timedelta(hours=3)

        params = {
            # Should return one that is created at (or very close to) some_point_in_time
            "created_before": some_point_in_time + timedelta(minutes=2),
            "created_after": some_point_in_time - timedelta(minutes=2),
        }

        result_ids = self._request_filter_signals(params)
        self.assertEqual(1, len(result_ids))

    def test_filter_combined_with_all_results(self):
        """ Test combination of created_before and created_after, union contains all signals """
        now = datetime.now()

        params = {
            # Should return one that is created at (or very close to) some_point_in_time
            "created_before": now + timedelta(minutes=2),
            "created_after": now - timedelta(days=30),
        }

        result_ids = self._request_filter_signals(params)
        self.assertEqual(20, len(result_ids))

    def test_filter_categories_slug(self):
        """ Test multiple slugs. Should return all signals that appear in either of the categories
        (OR) """
        slugs = [self.sub_categories[0].slug, self.sub_categories[1].slug]
        params = {
            "category_slug": slugs
        }

        result_ids = self._request_filter_signals(params)

        expected_cnt = len(slugs) * (len(self.signals) // len(self.sub_categories)) + (
            len(slugs) if len(
                self.signals) % len(self.sub_categories) > len(slugs) else len(self.signals) % len(
                self.sub_categories))

        self.assertEqual(expected_cnt, len(result_ids))

    def test_filter_maincategories_slug(self):
        """ Test multiple slugs. Should return all signals that appear in either of the categories
        (OR) """
        slugs = [self.sub_categories[0].parent.slug,
                 self.sub_categories[1].parent.slug]
        params = {
            "maincategory_slug": slugs
        }

        result_ids = self._request_filter_signals(params)

        expected_cnt = len(slugs) * (len(self.signals) // len(self.sub_categories)) + (
            len(slugs) if len(
                self.signals) % len(self.sub_categories) > len(slugs) else len(self.signals) % len(
                self.sub_categories))

        self.assertEqual(expected_cnt, len(result_ids))

    def test_filter_all_statuses(self):
        """ Test set of all used statuses (in this class). Should return all signals """
        statuses = ['m', 'b', 'h']
        params = {"status": statuses}

        result_ids = self._request_filter_signals(params)
        self.assertEqual(len(self.signals), len(result_ids))

    def test_filter_statuses_separate(self):
        """ Test result sets of statuses separately, and combined. """
        params = {"status": ['m']}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(self.states.count(GEMELD), len(result_ids))

        params = {"status": ['b']}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(self.states.count(BEHANDELING), len(result_ids))

        params = {"status": ['h']}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(self.states.count(ON_HOLD), len(result_ids))

        params = {"status": ['h', 'b']}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(self.states.count(ON_HOLD) + self.states.count(BEHANDELING),
                         len(result_ids))
