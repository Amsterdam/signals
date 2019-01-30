from datetime import datetime, timedelta

from django.db import connection
from rest_framework.test import APITestCase

from signals.apps.signals.models import CategoryAssignment, Signal, Status
from signals.apps.signals.workflow import BEHANDELING, ON_HOLD
from tests.apps.signals.factories import (
    LocationFactory,
    PriorityFactory,
    ReporterFactory,
    SignalFactory,
    StatusFactory,
    SubCategoryFactory
)
from tests.apps.users.factories import SuperUserFactory


class TestFilters(APITestCase):
    """ Tests filters on the private v1 list endpoint: /signals/v1/private/signals """
    SIGNALS_DISTRIBUTE_DAYS_CNT = 10
    SIGNALS_DISTRIBUTE_HOURS_CNT = 10
    SUBCATEGORY_CNT = 5
    LIST_ENDPOINT = '/signals/v1/private/signals/'

    signals = []
    sub_categories = []

    @classmethod
    def _create_signals(cls):
        cls.signals = [SignalFactory.create() for _ in
                       range(cls.SIGNALS_DISTRIBUTE_DAYS_CNT + cls.SIGNALS_DISTRIBUTE_HOURS_CNT)]

    @classmethod
    def _set_signal_created_updated_at(cls, signal_id: int, dt: datetime):
        """ Sets created_at and updated_at to dt for signal with signal_id """
        signals_tablename = Signal._meta.db_table

        query = "UPDATE {} SET created_at = %s, updated_at = %s WHERE signal_id=%s".format(
            signals_tablename)

        with connection.cursor() as cursor:
            cursor.execute(query, [dt, dt, signal_id])

    @classmethod
    def _distribute_signals_days(cls):
        """ Distributes SIGNALS_DISTRIBUTE_DAYS_CNT signals, one per day, from yesterday
        backwards """

        now = datetime.utcnow()

        for idx, signal in enumerate(cls.signals[:cls.SIGNALS_DISTRIBUTE_DAYS_CNT]):
            cls._set_signal_created_updated_at(signal.signal_id, now - timedelta(days=idx + 1))

    @classmethod
    def _distribute_signals_hours(cls):
        """ Distributes SIGNALS_DISTRIBUTE_HOURS_CNT signals, one per hour, starting at time now()
        going backwards """

        now = datetime.utcnow()

        frm = cls.SIGNALS_DISTRIBUTE_DAYS_CNT
        to = cls.SIGNALS_DISTRIBUTE_DAYS_CNT + cls.SIGNALS_DISTRIBUTE_HOURS_CNT
        for idx, signal in enumerate(cls.signals[frm:to]):
            cls._set_signal_created_updated_at(signal.signal_id, now - timedelta(hours=idx))

    @classmethod
    def _distribute_signals_categories(cls):
        """ Assigns created signals to new subcategories, round-robin """
        cls.sub_categories = [SubCategoryFactory.create() for _ in range(cls.SUBCATEGORY_CNT)]

        for idx, signal in enumerate(cls.signals):
            assignment = CategoryAssignment()
            assignment._signal = signal
            assignment.sub_category = cls.sub_categories[idx % len(cls.sub_categories)]
            assignment.save()
            signal.category_assignment = assignment
            signal.save()

    @classmethod
    def _assign_default_relations(cls):
        for signal in cls.signals:
            location = LocationFactory(_signal=signal)
            reporter = ReporterFactory(_signal=signal)
            priority = PriorityFactory(_signal=signal)
            status = StatusFactory(_signal=signal)
            signal.location = location
            signal.reporter = reporter
            signal.status = status
            signal.priority = priority
            signal.save()

    @classmethod
    def _change_statuses(cls):
        """ Changes status of 3 signals to BEHANDELING and 5 to ON_HOLD """

        # Create 3 BEHANDELING
        for signal in cls.signals[:3]:
            status = Status()
            status._signal = signal
            status.state = BEHANDELING
            status.save()

            signal.status = status
            signal.save()

        # Create 2 ON_HOLD
        for signal in cls.signals[3:5]:
            status = Status()
            status._signal = signal
            status.state = ON_HOLD
            status.save()

            signal.status = status
            signal.save()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_signals()
        cls._distribute_signals_categories()
        cls._assign_default_relations()
        cls._change_statuses()

        cls._distribute_signals_days()
        cls._distribute_signals_hours()

        cls.superuser = SuperUserFactory(username='superuser@example.com')

    def setUp(self):
        self.signals = TestFilters.signals
        self.sub_categories = TestFilters.sub_categories

    def _request_filter_signals(self, filter_params: dict):
        """ Does a filter request and returns the signal ID's present in the request """
        self.client.force_authenticate(user=self.superuser)
        resp = self.client.get(self.LIST_ENDPOINT, data=filter_params)

        self.assertEquals(200, resp.status_code)

        resp_json = resp.json()
        ids = [res["id"] for res in resp_json["results"]]

        self.assertEquals(resp_json["count"], len(ids))

        return ids

    def test_result_all(self):
        """ No filtering should return all """
        result_ids = self._request_filter_signals({})
        self.assertEquals(len(self.signals), len(result_ids))

    def test_filter_id(self):
        """ Filtering on id should return one signal """
        id = self.signals[0].id
        result_ids = self._request_filter_signals({"id": id})

        self.assertEquals(1, len(result_ids))
        self.assertListEqual([id], result_ids)

    def test_filter_updated_after(self):
        """ Test updated_after """
        now = datetime.now()

        params = {"updated_after": now - timedelta(hours=4, minutes=30)}
        result_ids = self._request_filter_signals(params)

        # Expect 5 results. now, now - 1, now - 2, now - 3, now - 4 hours
        self.assertEquals(5, len(result_ids))

    def test_filter_updated_before(self):
        """ Test updated_before """
        now = datetime.now()

        params = {"updated_before": now - timedelta(hours=18)}
        result_ids = self._request_filter_signals(params)

        # Expect 10 results
        self.assertEquals(10, len(result_ids))

    def test_filter_created_after(self):
        """ Test created_after """
        now = datetime.now()

        params = {"created_after": now - timedelta(minutes=30)}
        result_ids = self._request_filter_signals(params)

        self.assertEquals(1, len(result_ids))

    def test_filter_created_before(self):
        """ Test created_before """
        now = datetime.now()

        params = {"created_before": now - timedelta(days=8, hours=12)}
        result_ids = self._request_filter_signals(params)

        self.assertEquals(2, len(result_ids))

    def test_filter_combined_no_results(self):
        """ Test combination of created_before and created_after, distinct sets """
        some_point_in_time = datetime.now() - timedelta(hours=3)

        params = {
            # Should return nothing. Sets are distinct, so no results
            "created_before": some_point_in_time - timedelta(minutes=1),
            "created_after": some_point_in_time + timedelta(minutes=1),
        }

        result_ids = self._request_filter_signals(params)
        self.assertEquals(0, len(result_ids))

    def test_filter_combined_with_one_result(self):
        """ Test combination of created_before and created_after, union contains one signal """
        some_point_in_time = datetime.now() - timedelta(hours=3)

        params = {
            # Should return one that is created at (or very close to) some_point_in_time
            "created_before": some_point_in_time + timedelta(minutes=2),
            "created_after": some_point_in_time - timedelta(minutes=2),
        }

        result_ids = self._request_filter_signals(params)
        self.assertEquals(1, len(result_ids))

    def test_filter_combined_with_all_results(self):
        """ Test combination of created_before and created_after, union contains all signals """
        now = datetime.now()

        params = {
            # Should return one that is created at (or very close to) some_point_in_time
            "created_before": now + timedelta(minutes=2),
            "created_after": now - timedelta(days=30),
        }

        result_ids = self._request_filter_signals(params)
        self.assertEquals(20, len(result_ids))

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

        self.assertEquals(expected_cnt, len(result_ids))

    def test_filter_maincategories_slug(self):
        """ Test multiple slugs. Should return all signals that appear in either of the categories
        (OR) """
        slugs = [self.sub_categories[0].main_category.slug,
                 self.sub_categories[1].main_category.slug]
        params = {
            "maincategory_slug": slugs
        }

        result_ids = self._request_filter_signals(params)

        expected_cnt = len(slugs) * (len(self.signals) // len(self.sub_categories)) + (
            len(slugs) if len(
                self.signals) % len(self.sub_categories) > len(slugs) else len(self.signals) % len(
                self.sub_categories))

        self.assertEquals(expected_cnt, len(result_ids))

    def test_filter_all_statuses(self):
        """ Test set of all used statuses (in this class). Should return all signals """
        statuses = ['m', 'b', 'h']
        params = {"status": statuses}

        result_ids = self._request_filter_signals(params)
        self.assertEquals(20, len(result_ids))

    def test_filter_statuses_separate(self):
        """ Test result sets of statuses separately, and combined. """
        params = {"status": ['m']}
        result_ids = self._request_filter_signals(params)
        self.assertEquals(15, len(result_ids))

        params = {"status": ['b']}
        result_ids = self._request_filter_signals(params)
        self.assertEquals(3, len(result_ids))

        params = {"status": ['h']}
        result_ids = self._request_filter_signals(params)
        self.assertEquals(2, len(result_ids))

        params = {"status": ['h', 'b']}
        result_ids = self._request_filter_signals(params)
        self.assertEquals(5, len(result_ids))
