# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from datetime import datetime, timedelta
from random import shuffle

from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.utils import timezone
from freezegun import freeze_time

from signals.apps.feedback.factories import FeedbackFactory
from signals.apps.signals import workflow
from signals.apps.signals.factories import (
    AreaFactory,
    CategoryAssignmentFactory,
    CategoryFactory,
    DepartmentFactory,
    NoteFactory,
    ParentCategoryFactory,
    ServiceLevelObjectiveFactory,
    SignalDepartmentsFactory,
    SignalFactory,
    SignalUserFactory,
    SourceFactory,
    StatusFactory,
    TypeFactory
)
from signals.apps.signals.models import Priority, Signal, SignalDepartments
from signals.apps.signals.workflow import BEHANDELING, GEMELD, ON_HOLD
from signals.test.utils import SignalsBaseApiTestCase


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
        now = timezone.now()

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
        SourceFactory.create(name='online', is_public=True)
        SourceFactory.create(name='ACC')

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

    def test_filter_updated_after(self):
        """ Test updated_after """
        now = timezone.now()

        params = {"updated_after": now - timedelta(hours=4, minutes=30)}
        result_ids = self._request_filter_signals(params)

        # Expect 5 results. now, now - 1, now - 2, now - 3, now - 4 hours
        self.assertEqual(5, len(result_ids))

    def test_filter_updated_before(self):
        """ Test updated_before """
        now = timezone.now()

        params = {"updated_before": now - timedelta(hours=18)}
        result_ids = self._request_filter_signals(params)

        # Expect 10 results
        self.assertEqual(10, len(result_ids))

    def test_filter_created_after(self):
        """ Test created_after """
        now = timezone.now()

        params = {"created_after": now - timedelta(minutes=30)}
        result_ids = self._request_filter_signals(params)

        self.assertEqual(1, len(result_ids))

    def test_filter_created_before(self):
        """ Test created_before """
        now = timezone.now()

        params = {"created_before": now - timedelta(days=8, hours=12)}
        result_ids = self._request_filter_signals(params)

        self.assertEqual(2, len(result_ids))

    def test_filter_combined_no_results(self):
        """ Test combination of created_before and created_after, distinct sets """
        some_point_in_time = timezone.now() - timedelta(hours=3)

        params = {
            # Should return nothing. Sets are distinct, so no results
            "created_before": some_point_in_time - timedelta(minutes=1),
            "created_after": some_point_in_time + timedelta(minutes=1),
        }

        result_ids = self._request_filter_signals(params)
        self.assertEqual(0, len(result_ids))

    def test_filter_combined_with_one_result(self):
        """ Test combination of created_before and created_after, union contains one signal """
        some_point_in_time = timezone.now() - timedelta(hours=3)

        params = {
            # Should return one that is created at (or very close to) some_point_in_time
            "created_before": some_point_in_time + timedelta(minutes=2),
            "created_after": some_point_in_time - timedelta(minutes=2),
        }

        result_ids = self._request_filter_signals(params)
        self.assertEqual(1, len(result_ids))

    def test_filter_combined_with_all_results(self):
        """ Test combination of created_before and created_after, union contains all signals """
        now = timezone.now()

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

    def test_filter_feedback_not_received(self):
        feedback = FeedbackFactory.create(
            _signal=self.signals[0]
        )

        params = {'feedback': 'not_received'}
        result_ids = self._request_filter_signals(params)

        self.assertEqual(1, len(result_ids))
        self.assertEqual(feedback._signal_id, result_ids[0])

    def test_filter_feedback_positive_feedback(self):
        feedback = FeedbackFactory.create(
            _signal=self.signals[0],
            is_satisfied=True,
            submitted_at=timezone.now()
        )

        params = {'feedback': 'satisfied'}
        result_ids = self._request_filter_signals(params)

        self.assertEqual(1, len(result_ids))
        self.assertEqual(feedback._signal_id, result_ids[0])

    def test_filter_feedback_negative_feedback(self):
        feedback = FeedbackFactory.create(
            _signal=self.signals[0],
            is_satisfied=False,
            submitted_at=timezone.now()
        )

        params = {'feedback': 'not_satisfied'}
        result_ids = self._request_filter_signals(params)

        self.assertEqual(1, len(result_ids))
        self.assertEqual(feedback._signal_id, result_ids[0])

    def test_filter_feedback_multiple_last_positive(self):
        now = timezone.now()

        FeedbackFactory.create(
            _signal=self.signals[0],
            is_satisfied=False,
            submitted_at=now - timedelta(days=1)
        )

        feedback_positive = FeedbackFactory.create(
            _signal=self.signals[0],
            is_satisfied=True,
            submitted_at=now
        )

        params = {'feedback': 'not_satisfied'}
        result_ids = self._request_filter_signals(params)

        self.assertEqual(0, len(result_ids))

        params = {'feedback': 'satisfied'}
        result_ids = self._request_filter_signals(params)

        self.assertEqual(1, len(result_ids))
        self.assertEqual(feedback_positive._signal_id, result_ids[0])

    def test_filter_feedback_multiple_negative(self):
        now = timezone.now()

        FeedbackFactory.create(
            _signal=self.signals[0],
            is_satisfied=True,
            submitted_at=now - timedelta(days=1)
        )

        feedback_negative = FeedbackFactory.create(
            _signal=self.signals[0],
            is_satisfied=False,
            submitted_at=now
        )

        params = {'feedback': 'satisfied'}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(0, len(result_ids))

        params = {'feedback': 'not_satisfied'}
        result_ids = self._request_filter_signals(params)

        self.assertEqual(1, len(result_ids))
        self.assertEqual(feedback_negative._signal_id, result_ids[0])

    def test_filter_feedback_multiple_latest_not_received(self):
        now = timezone.now()

        FeedbackFactory.create(
            _signal=self.signals[0],
            is_satisfied=True,
            submitted_at=now - timedelta(days=1)
        )

        feedback_negative = FeedbackFactory.create(
            _signal=self.signals[0]
        )

        params = {'feedback': 'not_satisfied'}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(0, len(result_ids))

        params = {'feedback': 'satisfied'}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(0, len(result_ids))

        params = {'feedback': 'not_received'}
        result_ids = self._request_filter_signals(params)

        self.assertEqual(1, len(result_ids))
        self.assertEqual(feedback_negative._signal_id, result_ids[0])

    def test_filter_source(self):
        result_ids = self._request_filter_signals({'source': 'online'})
        self.assertEqual(len(self.signals), len(result_ids))

    def test_filter_source_multiple_sources(self):
        acc_signals = SignalFactory.create_batch(5, source='ACC')

        result_ids = self._request_filter_signals({'source': 'online'})
        self.assertEqual(len(self.signals), len(result_ids))

        result_ids = self._request_filter_signals({'source': 'ACC'})
        self.assertEqual(len(acc_signals), len(result_ids))

    def test_filter_source_invalid_option(self):
        self.client.force_authenticate(user=self.superuser)
        resp = self.client.get(self.LIST_ENDPOINT, data={'source': 'invalid'})
        self.assertEqual(400, resp.status_code)
        self.assertEqual(resp.json()['source'][0],
                         'Selecteer een geldige keuze. invalid is geen beschikbare keuze.')

    def test_filter_maincategory_and_category_slugs(self):
        maincategory_slugs = [
            self.sub_categories[2].parent.slug,
            self.sub_categories[3].parent.slug
        ]

        category_slugs = [
            self.sub_categories[0].slug,
            self.sub_categories[1].slug
        ]

        params = {
            'maincategory_slug': maincategory_slugs,
            'category_slug': category_slugs
        }

        result_ids = self._request_filter_signals(params)
        self.assertEqual(16, len(result_ids))

    def test_filter_maincategory_and_category_slugs_not_a_unique_slug(self):
        parent_category = ParentCategoryFactory.create(name='not_unique')
        category = CategoryFactory.create(name='not_unique', parent=parent_category)

        SignalFactory.create(category_assignment__category=category)

        params = {
            'maincategory_slug': [parent_category.slug, ],
            'category_slug': [category.slug, ]
        }

        result_ids = self._request_filter_signals(params)
        self.assertEqual(1, len(result_ids))

    def test_filter_kind_parent_signal(self):
        """
        Filter Signals that are a parent Signal (2 parent Signals are created so we expect 2)
        """
        parent_one = SignalFactory.create()
        SignalFactory.create_batch(2, parent=parent_one)

        parent_two = SignalFactory.create()
        SignalFactory.create_batch(2, parent=parent_two)

        params = {'kind': 'parent_signal'}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(2, len(result_ids))

    def test_filter_kind_no_parent_signal(self):
        """
        Filter Signals that are a parent Signal (None are created so we expect 0)
        """
        params = {'kind': 'parent_signal'}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(0, len(result_ids))

    def test_filter_kind_child_signal(self):
        """
        Filter Signals that are a child Signal (3 child Signals are created so we expect 3)
        """
        parent_one = SignalFactory.create()
        SignalFactory.create_batch(1, parent=parent_one)

        parent_two = SignalFactory.create()
        SignalFactory.create_batch(2, parent=parent_two)

        params = {'kind': 'child_signal'}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(3, len(result_ids))

    def test_filter_kind_no_child_signal(self):
        """
        Filter Signals that are a child Signal (None are created so we expect 0)
        """
        params = {'kind': 'child_signal'}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(0, len(result_ids))

    def test_filter_kind_signal(self):
        """
        We expect only "normal" Signals
        """
        parent_one = SignalFactory.create()
        SignalFactory.create_batch(1, parent=parent_one)

        parent_two = SignalFactory.create()
        SignalFactory.create_batch(2, parent=parent_two)

        params = {'kind': 'signal'}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(20, len(result_ids))

    def test_filter_kind_exclude_parent_signal(self):
        """
        We expect only "normal" and "child" Signals
        """
        parent_one = SignalFactory.create()
        SignalFactory.create_batch(1, parent=parent_one)

        parent_two = SignalFactory.create()
        SignalFactory.create_batch(2, parent=parent_two)

        params = {'kind': 'exclude_parent_signal'}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(23, len(result_ids))

    def test_filter_directing_department_null(self):
        parent_one = SignalFactory.create()
        SignalFactory.create_batch(1, parent=parent_one)

        params = {'directing_department': 'null'}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(1, len(result_ids))

    def test_filter_directing_department_null_with_other_relations(self):
        parent_one = SignalFactory.create()
        SignalFactory.create_batch(1, parent=parent_one)

        directing_departments = SignalDepartments.objects.create(
            _signal=parent_one,
            created_by='test@example.com',
            relation_type='routing'
        )
        directing_departments.save()
        parent_one.directing_departments_assignment = directing_departments

        params = {'directing_department': 'null'}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(1, len(result_ids))

    def test_filter_directing_department_null_empty_directing(self):
        parent_one = SignalFactory.create()
        SignalFactory.create_batch(1, parent=parent_one)

        directing_departments = SignalDepartments.objects.create(
            _signal=parent_one,
            created_by='test@example.com',
            relation_type='directing'
        )
        directing_departments.save()
        parent_one.directing_departments_assignment = directing_departments

        params = {'directing_department': 'null'}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(1, len(result_ids))

    def test_filter_directing_department(self):
        department = DepartmentFactory.create()

        parent_one = SignalFactory.create()
        SignalFactory.create_batch(1, parent=parent_one)

        directing_departments = SignalDepartments.objects.create(
            _signal=parent_one,
            created_by='test@example.com',
            relation_type='directing'
        )
        directing_departments.departments.add(department)
        directing_departments.save()
        parent_one.directing_departments_assignment = directing_departments
        parent_one.save()
        params = {'directing_department': department.code}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(1, len(result_ids))

    def test_filter_directing_department_mixed(self):
        department = DepartmentFactory.create()

        parent_one = SignalFactory.create()
        SignalFactory.create_batch(1, parent=parent_one)

        directing_departments = SignalDepartments.objects.create(
            _signal=parent_one,
            created_by='test@example.com',
            relation_type='directing'
        )

        directing_departments.departments.add(department)
        directing_departments.save()
        parent_one.directing_departments_assignment = directing_departments
        parent_one.save()

        parent_two = SignalFactory.create()
        SignalFactory.create_batch(2, parent=parent_two)

        params = {'directing_department': ['null', department.code]}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(2, len(result_ids))

    def test_SIG_3390_filter_directing_department(self):
        department = DepartmentFactory.create()

        parent_one = SignalFactory.create()
        SignalFactory.create_batch(1, parent=parent_one)

        directing_departments = SignalDepartments.objects.create(
            _signal=parent_one,
            created_by='test@example.com',
            relation_type='directing'
        )

        directing_departments.departments.add(department)
        directing_departments.save()
        parent_one.directing_departments_assignment = directing_departments
        parent_one.save()

        parent_two = SignalFactory.create()
        SignalFactory.create_batch(2, parent=parent_two)

        parent_three = SignalFactory.create()

        directing_departments = SignalDepartments.objects.create(
            _signal=parent_three,
            created_by='test@example.com',
            relation_type='directing'
        )

        parent_three.directing_departments_assignment = directing_departments
        parent_three.save()

        SignalFactory.create_batch(2, parent=parent_three)

        params = {'directing_department': ['null', department.code]}
        result_ids = self._request_filter_signals(params)
        self.assertEqual(3, len(result_ids))

    def test_filter_category_id(self):
        """
        Test the category_id filter. When the ID of a category is know there is no need to filter by slug(s) we can just
        use the category_id to filter on.
        """
        params = {'category_id': [
            self.signals[0].category_assignment.category.id,
            self.signals[1].category_assignment.category.id,
        ]}
        result_ids = self._request_filter_signals(params)

        expected_cnt = len([
            signal for signal in self.signals if signal.category_assignment.category.id in params['category_id']
        ])
        self.assertEqual(expected_cnt, len(result_ids))


class TestPriorityFilter(SignalsBaseApiTestCase):
    LIST_ENDPOINT = '/signals/v1/private/signals/'

    def _request_filter_signals(self, filter_params: dict):
        """ Does a filter request and returns the signal ID's present in the request """
        self.client.force_authenticate(user=self.superuser)
        resp = self.client.get(self.LIST_ENDPOINT, data=filter_params)

        self.assertEqual(200, resp.status_code)

        resp_json = resp.json()
        ids = [res["id"] for res in resp_json["results"]]

        self.assertEqual(resp_json["count"], len(ids))

        return ids

    def setUp(self):
        self.priority_low = SignalFactory.create(priority__priority=Priority.PRIORITY_LOW)
        self.priority_high = SignalFactory.create(priority__priority=Priority.PRIORITY_HIGH)
        self.priority_normal = SignalFactory.create(priority__priority=Priority.PRIORITY_NORMAL)

    def test_priority_filter_single_value(self):
        """Test original filter behavior, is used in the wild, must work."""
        filter_params = {'priority': Priority.PRIORITY_LOW}
        self.assertEqual(
            self._request_filter_signals(filter_params),
            [self.priority_low.id]
        )

        # test all possibilities
        for signal in [self.priority_low, self.priority_normal, self.priority_high]:
            filter_params = {'priority': signal.priority.priority}
            self.assertEqual(
                self._request_filter_signals(filter_params),
                [signal.id]
            )

    def test_priority_filter_multiple_values(self):
        """Allow several priority values, see SIG-2187."""
        filter_params = {'priority': [
            Priority.PRIORITY_LOW,
            Priority.PRIORITY_NORMAL,
            Priority.PRIORITY_HIGH,
        ]}
        ids = set(self._request_filter_signals(filter_params))
        self.assertEqual(len(ids), 3)


class TestNoteKeywordFilter(SignalsBaseApiTestCase):
    LIST_ENDPOINT = '/signals/v1/private/signals/'

    def _request_filter_signals(self, filter_params: dict):
        """ Does a filter request and returns the signal ID's present in the request """
        self.client.force_authenticate(user=self.superuser)
        resp = self.client.get(self.LIST_ENDPOINT, data=filter_params)

        self.assertEqual(200, resp.status_code)

        resp_json = resp.json()
        ids = [res["id"] for res in resp_json["results"]]

        self.assertEqual(resp_json["count"], len(ids))

        return ids

    def setUp(self):
        self.keyword = 'KEYWORD'
        text_no_keyword = 'blah blah blah'
        text_with_keyword = f'blah blah blah {self.keyword} blah blah blah'

        self.signal_with_keyword = SignalFactory()
        NoteFactory(_signal=self.signal_with_keyword, text=text_no_keyword)
        NoteFactory(_signal=self.signal_with_keyword, text=text_no_keyword)
        NoteFactory(_signal=self.signal_with_keyword, text=text_with_keyword)
        NoteFactory(_signal=self.signal_with_keyword, text=text_with_keyword)

        self.signal_no_keyword = SignalFactory()
        NoteFactory(_signal=self.signal_with_keyword, text=text_no_keyword)

    def test_retrieve_signal_with_keyword(self):
        filter_params = {'note_keyword': self.keyword}
        ids = self._request_filter_signals(filter_params)
        self.assertEqual(ids, [self.signal_with_keyword.id])

        filter_params = {'note_keyword': 'NOT PRESENT'}
        ids = self._request_filter_signals(filter_params)
        self.assertEqual(ids, [])


class TestContactDetailsPresentFilter(SignalsBaseApiTestCase):
    SIGNALS_LIST_ENDPOINT = '/signals/v1/private/signals/'
    STORED_FILTERS_LIST_ENDPOINT = '/signals/v1/private/me/filters/'
    STORED_FILTERS_DETAIL_ENDPOINT = '/signals/v1/private/me/filters/{pk}'
    GEOGRAPHY_ENDPOINT = '/signals/v1/private/signals/geography'

    def _request_filter_signals(self, filter_params: dict):
        """ Does a filter request and returns the signal ID's present in the request """
        self.client.force_authenticate(user=self.superuser)
        resp = self.client.get(self.SIGNALS_LIST_ENDPOINT, data=filter_params)

        self.assertEqual(200, resp.status_code)

        resp_json = resp.json()
        ids = [res["id"] for res in resp_json["results"]]

        self.assertEqual(resp_json["count"], len(ids))

        return ids

    def _request_geo_filter_signals(self, filter_params: dict):
        """ Does a filter request and returns the signal ID's present in the request """
        self.client.force_authenticate(user=self.superuser)
        resp = self.client.get(self.GEOGRAPHY_ENDPOINT, data=filter_params)

        self.assertEqual(200, resp.status_code)

        resp_json = resp.json()
        ids = [res['properties']['id'] for res in resp_json['features']]

        self.assertEqual(len(resp_json['features']), len(ids))

        return ids

    def setUp(self):
        self.signal_anonymous = SignalFactory.create(reporter__phone='', reporter__email='')
        self.signal_has_email = SignalFactory.create(
            reporter__phone='', reporter__email='test@example.com')
        self.signal_has_phone = SignalFactory.create(
            reporter__phone='0123456789', reporter__email='')
        self.signal_has_both = SignalFactory.create(
            reporter__phone='0123456789', reporter__email='test@example.com')

    def test_contact_details_none(self):
        filter_params = {'contact_details': ['none']}
        ids = self._request_filter_signals(filter_params)

        self.assertEqual(len(ids), 1)
        self.assertEqual(set(ids), set([self.signal_anonymous.id]))

    def test_geo_contact_details_none(self):
        filter_params = {'contact_details': ['none']}
        ids = self._request_geo_filter_signals(filter_params)

        self.assertEqual(len(ids), 1)
        self.assertEqual(set(ids), set([self.signal_anonymous.id]))

    def test_contact_details_email(self):
        filter_params = {'contact_details': ['email']}
        ids = self._request_filter_signals(filter_params)

        self.assertEqual(len(ids), 2)
        self.assertEqual(set(ids), set([self.signal_has_email.id, self.signal_has_both.id]))

    def test_geo_contact_details_email(self):
        filter_params = {'contact_details': ['email']}
        ids = self._request_geo_filter_signals(filter_params)

        self.assertEqual(len(ids), 2)
        self.assertEqual(set(ids), set([self.signal_has_email.id, self.signal_has_both.id]))

    def test_contact_details_phone(self):
        filter_params = {'contact_details': ['phone']}
        ids = self._request_filter_signals(filter_params)

        self.assertEqual(len(ids), 2)
        self.assertEqual(set(ids), set([self.signal_has_phone.id, self.signal_has_both.id]))

    def test_geo_contact_details_phone(self):
        filter_params = {'contact_details': ['phone']}
        ids = self._request_geo_filter_signals(filter_params)

        self.assertEqual(len(ids), 2)
        self.assertEqual(set(ids), set([self.signal_has_phone.id, self.signal_has_both.id]))

    def test_contact_details_combination(self):
        filter_params = {'contact_details': ['none', 'email', 'phone']}
        ids = self._request_filter_signals(filter_params)
        geo_ids = self._request_geo_filter_signals(filter_params)

        self.assertEqual(len(ids), 4)
        self.assertEqual(len(geo_ids), 4)

    def test_contact_details_bad_inputs(self):
        BAD_INPUTS = [
            {'contact_details': ['GARBAGE']},  # not a choice
            {'contact_details': ['none', 'email', 'GARBAGE']},  # one bad choice
        ]

        for filter_params in BAD_INPUTS:
            self.client.force_authenticate(user=self.superuser)
            response = self.client.get(self.SIGNALS_LIST_ENDPOINT, data=filter_params)
            self.assertEqual(response.status_code, 400)

    def test_contact_details_store_and_retrieve(self):
        filter_name = 'Bewaarde contact details filter.'
        data = {
            'name': filter_name,
            'options': {
                'contact_details': ['none', 'email']
            }
        }

        # Store our filter for later use
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(self.STORED_FILTERS_LIST_ENDPOINT, data, format='json')

        self.assertEqual(201, response.status_code)
        response_data = response.json()
        pk = response_data['id']

        # Retrieve our filter and use it to filter signals
        response = self.client.get(self.STORED_FILTERS_DETAIL_ENDPOINT.format(pk=pk))
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data['name'], filter_name)
        self.assertIn('contact_details', response_data['options'])
        self.assertEqual(
            set(response_data['options']['contact_details']), set(['none', 'email']))


class TestTypeFilter(SignalsBaseApiTestCase):
    SIGNALS_LIST_ENDPOINT = '/signals/v1/private/signals/'
    GEOGRAPHY_ENDPOINT = '/signals/v1/private/signals/geography'

    def setUp(self):
        self.signals = {
            'SIG': SignalFactory.create_batch(5),
            'REQ': SignalFactory.create_batch(3),
            'QUE': SignalFactory.create_batch(1),
            'COM': SignalFactory.create_batch(2),
            'MAI': SignalFactory.create_batch(4),
        }

        hours = 1
        for type_code in self.signals.keys():
            with freeze_time(timezone.now() + timedelta(hours=hours)):
                for signal in self.signals[type_code]:
                    signal_type = TypeFactory.create(_signal=signal, name=type_code)
                    signal.type_assignment = signal_type
                    signal.save()
            hours += 1

    def test_filter_single_type(self):
        self.client.force_authenticate(user=self.superuser)

        for filter_option in self.signals:
            response = self.client.get(self.SIGNALS_LIST_ENDPOINT, data={'type': [filter_option]})

            self.assertEqual(200, response.status_code)

            response_data = response.json()
            self.assertEqual(response_data['count'], len(self.signals[filter_option]))

            signal_ids = [signal.id for signal in self.signals[filter_option]]
            response_ids = [response_item['id'] for response_item in response_data['results']]
            response_type_codes = [response_item['type']['code'] for response_item in response_data['results']]

            self.assertEqual(len(signal_ids), len(response_ids))
            self.assertEqual(set(signal_ids), set(response_ids))
            self.assertEqual(1, len(set(response_type_codes)))
            self.assertEqual({filter_option}, set(response_type_codes))

    def test_filter_geo_single_type(self):
        self.client.force_authenticate(user=self.superuser)

        for filter_option in self.signals:
            response = self.client.get(self.GEOGRAPHY_ENDPOINT, data={'type': [filter_option]})

            self.assertEqual(200, response.status_code)

            response_data = response.json()
            self.assertEqual(len(response_data['features']), len(self.signals[filter_option]))

            signal_ids = [signal.id for signal in self.signals[filter_option]]
            response_ids = [response_item['properties']['id'] for response_item in response_data['features']]

            self.assertEqual(len(signal_ids), len(response_ids))
            self.assertEqual(set(signal_ids), set(response_ids))

    def test_filter_multiple_types(self):
        self.client.force_authenticate(user=self.superuser)

        type_codes = ['COM', 'REQ']
        response = self.client.get(self.SIGNALS_LIST_ENDPOINT, data={'type': type_codes})
        self.assertEqual(200, response.status_code)

        response_data = response.json()
        self.assertEqual(response_data['count'], len(self.signals['COM']) + len(self.signals['REQ']))

        signal_ids = [signal.id for signal in self.signals['COM']] + [signal.id for signal in self.signals['REQ']]
        response_ids = [response_item['id'] for response_item in response_data['results']]
        response_type_codes = [response_item['type']['code'] for response_item in response_data['results']]

        self.assertEqual(len(signal_ids), len(response_ids))
        self.assertEqual(set(signal_ids), set(response_ids))
        self.assertEqual(2, len(set(response_type_codes)))
        self.assertEqual(set(type_codes), set(response_type_codes))

    def test_filter_geo_multiple_types(self):
        self.client.force_authenticate(user=self.superuser)

        type_codes = ['COM', 'REQ']
        response = self.client.get(self.GEOGRAPHY_ENDPOINT, data={'type': type_codes})
        self.assertEqual(200, response.status_code)

        response_data = response.json()
        self.assertEqual(len(response_data['features']), len(self.signals['COM']) + len(self.signals['REQ']))

        signal_ids = [signal.id for signal in self.signals['COM']] + [signal.id for signal in self.signals['REQ']]
        response_ids = [response_item['properties']['id'] for response_item in response_data['features']]

        self.assertEqual(len(signal_ids), len(response_ids))
        self.assertEqual(set(signal_ids), set(response_ids))


class TestAreaFilter(SignalsBaseApiTestCase):
    LIST_ENDPOINT = '/signals/v1/private/signals/'

    def _request_filter_signals(self, filter_params: dict):
        """ Does a filter request and returns the signal ID's present in the request """
        self.client.force_authenticate(user=self.superuser)

        resp = self.client.get(self.LIST_ENDPOINT, data=filter_params)

        self.assertEqual(200, resp.status_code)

        resp_json = resp.json()
        ids = [res["id"] for res in resp_json["results"]]

        self.assertEqual(resp_json["count"], len(ids))

        return ids

    def setUp(self):
        geometry = MultiPolygon([Polygon.from_bbox([4.877157, 52.357204, 4.929686, 52.385239])], srid=4326)
        self.pt_in_center = Point(4.88, 52.36)
        self.pt_out_center = Point(6, 53)

        self.area = AreaFactory.create(geometry=geometry, name='Centrum', code='centrum', _type__code='district')
        SignalFactory.create(
            location__geometrie=self.pt_in_center,
            location__area_code=self.area.code,
            location__area_type_code=self.area._type.code,
        )
        # no area code, but with geo location
        SignalFactory.create(location__geometrie=self.pt_out_center)

    def test_filter_areas(self):
        # all
        result_ids = self._request_filter_signals({})
        self.assertEqual(2, len(result_ids))
        # only non-assigned
        result_ids = self._request_filter_signals({'area_code': 'null'})
        self.assertEqual(1, len(result_ids))
        # filter on type_code
        result_ids = self._request_filter_signals({'area_type_code': 'district'})
        self.assertEqual(1, len(result_ids))
        # filter on type_code or area code
        result_ids = self._request_filter_signals({'area_code': self.area.code})
        self.assertEqual(1, len(result_ids))
        # filter on both
        result_ids = self._request_filter_signals({'area_type_code': 'district', 'area_code': self.area.code})
        self.assertEqual(1, len(result_ids))

    def test_filter_area_code_null(self):
        # Demonstrate problem behind Signalen #118
        result_ids = self._request_filter_signals({'area_type_code': 'null'})
        self.assertEqual(1, len(result_ids))


class TestParentSignalFilter(SignalsBaseApiTestCase):
    LIST_ENDPOINT = '/signals/v1/private/signals/'

    def _request_filter_signals(self, filter_params: dict):
        """ Does a filter request and returns the signal ID's present in the request """
        self.client.force_authenticate(user=self.superuser)
        resp = self.client.get(self.LIST_ENDPOINT, data=filter_params)

        self.assertEqual(200, resp.status_code)

        resp_json = resp.json()
        ids = [res["id"] for res in resp_json["results"]]

        self.assertEqual(resp_json["count"], len(ids))

        return ids

    def test_retrieve_all_parents_with_changes_in_one_of_the_children(self):
        now = timezone.now()

        parent_signal_to_keep = SignalFactory.create()
        for hour in range(5):
            # Create 4 child signals 1 hour apart
            with freeze_time(now + timedelta(hours=hour)):
                SignalFactory.create(parent=parent_signal_to_keep)

        with freeze_time(now + timedelta(hours=3)):
            # This way we have 1 child signal changed after the last update on the parent signal
            Signal.actions.update_status(data={'text': 'test', 'state': 'b'}, signal=parent_signal_to_keep)

        # This parent should not show up in the filter
        parent_signal_to_reject = SignalFactory.create()
        for hour in range(5):
            # Create 4 child signals 1 hour apart
            with freeze_time(now + timedelta(hours=hour)):
                SignalFactory.create(parent=parent_signal_to_reject)

        with freeze_time(now + timedelta(hours=6)):
            # This way the parent signal is changed last
            parent_signal_to_reject.save()

        filter_params = {'has_changed_children': True}
        ids = self._request_filter_signals(filter_params)
        self.assertEqual(len(ids), 1)
        self.assertEqual(ids, [parent_signal_to_keep.id])

    def test_retrieve_all_parents_with_no_changes_in_children(self):
        now = timezone.now()

        parent_signal_to_keep = SignalFactory.create()
        for hour in range(5):
            # Create 4 child signals 1 hour apart
            with freeze_time(now + timedelta(hours=hour)):
                SignalFactory.create(parent=parent_signal_to_keep)

        with freeze_time(now + timedelta(hours=6)):
            # This way the parent signal is changed last
            Signal.actions.update_status(data={'text': 'test', 'state': 'b'}, signal=parent_signal_to_keep)

        # This parent should not show up in the filter
        parent_signal_to_reject = SignalFactory.create()
        for hour in range(5):
            # Create 4 child signals 1 hour apart
            with freeze_time(now + timedelta(hours=hour)):
                SignalFactory.create(parent=parent_signal_to_reject)

        with freeze_time(now + timedelta(hours=3)):
            # This way we have 1 child signal changed after the last update on the parent signal
            Signal.actions.update_status(data={'text': 'test', 'state': 'b'}, signal=parent_signal_to_reject)

        filter_params = {'has_changed_children': 'False'}
        ids = self._request_filter_signals(filter_params)
        self.assertEqual(len(ids), 1)
        self.assertEqual(ids, [parent_signal_to_keep.id])

    def test_retrieve_mixed_signals(self):
        # A bunch of normal signals that should never be retrieved by this filter
        SignalFactory.create_batch(5)

        now = timezone.now()
        with freeze_time(now - timedelta(hours=1)):
            parents_with_changes = SignalFactory.create_batch(3)
            parents_without_changes = SignalFactory.create_batch(2)

        with freeze_time(now):
            for parent_signal in parents_with_changes:
                SignalFactory(parent=parent_signal)

            for parent_signal in parents_without_changes:
                SignalFactory(parent=parent_signal)

        with freeze_time(now + timedelta(hours=1)):
            for parent_signal in parents_without_changes:
                parent_signal.save()

        filter_params = {'has_changed_children': True}
        ids = self._request_filter_signals(filter_params)
        self.assertEqual(len(ids), len(parents_with_changes))
        self.assertEqual(set(ids), set([parent_signal.id for parent_signal in parents_with_changes]))

        filter_params = {'has_changed_children': False}
        ids = self._request_filter_signals(filter_params)
        self.assertEqual(len(ids), len(parents_without_changes))
        self.assertEqual(set(ids), set([parent_signal.id for parent_signal in parents_without_changes]))

    def test_retrieve_multiple(self):
        now = timezone.now()
        with freeze_time(now - timedelta(hours=1)):
            parents_with_changes = SignalFactory.create_batch(3)
            parents_without_changes = SignalFactory.create_batch(2)

        with freeze_time(now):
            for parent_signal in parents_with_changes:
                SignalFactory(parent=parent_signal)

            for parent_signal in parents_without_changes:
                SignalFactory(parent=parent_signal)

        with freeze_time(now + timedelta(hours=1)):
            for parent_signal in parents_without_changes:
                parent_signal.save()

        filter_params = {'has_changed_children': ['true', 0]}
        ids = self._request_filter_signals(filter_params)
        self.assertEqual(len(ids), len(parents_with_changes) + len(parents_without_changes))


class TestAssignedUserEmailFilter(SignalsBaseApiTestCase):
    LIST_ENDPOINT = '/signals/v1/private/signals/'

    def _request_filter_signals(self, filter_params: dict):
        """ Does a filter request and returns the signal ID's present in the request """
        self.client.force_authenticate(user=self.superuser)
        resp = self.client.get(self.LIST_ENDPOINT, data=filter_params)

        self.assertEqual(200, resp.status_code)

        resp_json = resp.json()
        ids = [res["id"] for res in resp_json["results"]]

        self.assertEqual(resp_json["count"], len(ids))

        return ids

    def setUp(self):
        self.signal0 = SignalFactory.create()
        self.signal1 = SignalFactory.create()
        self.signal2 = SignalFactory.create()
        self.su1 = SignalUserFactory.create(_signal=self.signal1)
        self.su2 = SignalUserFactory.create(_signal=self.signal2)
        self.signal1.user_assignment = self.su1
        self.signal2.user_assignment = self.su2
        self.signal1.save()
        self.signal2.save()

    def test_filter_assigned_user_email(self):
        # all
        result_ids = self._request_filter_signals({})
        self.assertEqual(3, len(result_ids))
        # filter on test1@example.com
        result_ids = self._request_filter_signals({'assigned_user_email': f'{self.su1.user.email}'})
        self.assertEqual(1, len(result_ids))
        self.assertTrue(self.signal1.id in result_ids)
        # filter on non-assigned
        result_ids = self._request_filter_signals({'assigned_user_email': 'null'})
        self.assertEqual(1, len(result_ids))
        self.assertTrue(self.signal0.id in result_ids)


class TestSignalDepartmentRoutingFilter(SignalsBaseApiTestCase):
    LIST_ENDPOINT = '/signals/v1/private/signals/'

    def _request_filter_signals(self, filter_params: dict):
        """ Does a filter request and returns the signal ID's present in the request """
        self.client.force_authenticate(user=self.superuser)
        resp = self.client.get(self.LIST_ENDPOINT, data=filter_params)

        self.assertEqual(200, resp.status_code)

        resp_json = resp.json()
        ids = [res["id"] for res in resp_json["results"]]

        self.assertEqual(resp_json["count"], len(ids))

        return ids

    def setUp(self):
        self.signal0 = SignalFactory.create()
        self.signal1 = SignalFactory.create()
        self.signal2 = SignalFactory.create()
        self.dep1 = DepartmentFactory.create()
        self.dep2 = DepartmentFactory.create()

        rel1 = SignalDepartmentsFactory.create(
            _signal=self.signal1,
            relation_type=SignalDepartments.REL_ROUTING,
            departments=[self.dep1])

        rel2 = SignalDepartmentsFactory.create(
            _signal=self.signal2,
            relation_type=SignalDepartments.REL_ROUTING,
            departments=[self.dep2])

        self.signal1.routing_assignment = rel1
        self.signal2.routing_assignment = rel2
        self.signal1.save()
        self.signal2.save()

    def test_filter_assigned_routing_department(self):
        # all
        result_ids = self._request_filter_signals({})
        self.assertEqual(3, len(result_ids))
        # filter on dep1 code
        result_ids = self._request_filter_signals({'routing_department_code': f'{self.dep1.code}'})
        self.assertEqual(1, len(result_ids))
        self.assertTrue(self.signal1.id in result_ids)
        # mutiple choice
        result_ids = self._request_filter_signals({'routing_department_code': [self.dep1.code, self.dep2.code]})
        self.assertEqual(2, len(result_ids))
        self.assertTrue(self.signal1.id in result_ids)
        # filter on non-assigned
        result_ids = self._request_filter_signals({'routing_department_code': 'null'})
        self.assertEqual(1, len(result_ids))
        self.assertTrue(self.signal0.id in result_ids)


class TestReporterEmailFilter(SignalsBaseApiTestCase):
    LIST_ENDPOINT = '/signals/v1/private/signals/'

    def _request_filter_signals(self, filter_params: dict):
        """ Does a filter request and returns the signal ID's present in the request """
        self.client.force_authenticate(user=self.superuser)
        resp = self.client.get(self.LIST_ENDPOINT, data=filter_params)

        self.assertEqual(200, resp.status_code)

        resp_json = resp.json()
        ids = [res["id"] for res in resp_json["results"]]

        self.assertEqual(resp_json["count"], len(ids))

        return ids

    def setUp(self):
        self.signal_to_keep = SignalFactory.create(reporter__email='keep@example.com')
        self.signal_to_reject = SignalFactory.create(reporter__email='reject@example.com')

    def test_filter_reporter_email(self):
        result_ids = self._request_filter_signals({'reporter_email': 'keep@example.com'})
        self.assertEqual(1, len(result_ids))
        self.assertEqual([self.signal_to_keep.id], result_ids)

    def test_filter_reporter_email_capitalized(self):
        result_ids = self._request_filter_signals({'reporter_email': 'KEEP@exaMple.Com'})
        self.assertEqual(1, len(result_ids))
        self.assertEqual([self.signal_to_keep.id], result_ids)

    def test_filter_after_anonymization(self):
        result_ids = self._request_filter_signals({'reporter_email': 'reject@example.com'})
        self.assertEqual(1, len(result_ids))
        self.assertEqual([self.signal_to_reject.id], result_ids)

        # anonymize signal, make sure it is no longer retrieved
        self.signal_to_reject.reporter.anonymize()
        result_ids = self._request_filter_signals({'reporter_email': 'reject@example.com'})
        self.assertEqual(0, len(result_ids))


class TestPunctualityFilter(SignalsBaseApiTestCase):
    LIST_ENDPOINT = '/signals/v1/private/signals/'

    def _request_filter_signals(self, filter_params: dict):
        """ Does a filter request and returns the signal ID's present in the request """
        self.client.force_authenticate(user=self.superuser)
        resp = self.client.get(self.LIST_ENDPOINT, data=filter_params)

        self.assertEqual(200, resp.status_code)

        resp_json = resp.json()
        ids = [res["id"] for res in resp_json["results"]]

        self.assertEqual(resp_json["count"], len(ids))

        return ids

    def setUp(self):
        # Test case uses signals that were created at 12:00 on a Friday and
        # have a either no SLO, a SLO of 1 calendar day, or a SLO of 1 working
        # days.
        tzinfo = timezone.get_default_timezone()

        self.cat_no_slo = CategoryFactory.create()
        self.cat_slo_w = CategoryFactory.create()
        self.slo_w = ServiceLevelObjectiveFactory.create(
            n_days=1, use_calendar_days=False, category=self.cat_slo_w)
        self.cat_slo_c = CategoryFactory.create()
        self.slo_c = ServiceLevelObjectiveFactory.create(
            n_days=1, use_calendar_days=True, category=self.cat_slo_c)

        self.created_at = datetime(2021, 2, 19, 12, 0, 0, tzinfo=tzinfo)
        with freeze_time(self.created_at):
            self.assertEqual(datetime.now(tz=tzinfo), self.created_at)
            # State workflow.AFGEHANDELD, workflow.GEANNULEERD and
            # workflow.GESPLITST cannot be late because work on them finished.
            self.signal_no_slo = SignalFactory.create(
                category_assignment__category=self.cat_no_slo, status__state=workflow.GEMELD)
            self.signal_no_slo_2 = SignalFactory.create(
                category_assignment__category=self.cat_no_slo, status__state=workflow.AFGEHANDELD)
            self.signal_slo_w = SignalFactory.create(
                category_assignment__category=self.cat_slo_w, status__state=workflow.GEMELD)
            self.signal_slo_w_2 = SignalFactory.create(
                category_assignment__category=self.cat_slo_w, status__state=workflow.AFGEHANDELD)
            self.signal_slo_c = SignalFactory.create(
                category_assignment__category=self.cat_slo_c, status__state=workflow.GEMELD)
            self.signal_slo_c_2 = SignalFactory.create(
                category_assignment__category=self.cat_slo_c, status__state=workflow.AFGEHANDELD)

    def test_filter_null(self):
        params = {'punctuality': 'null'}
        with freeze_time(self.created_at + timedelta(seconds=60)):
            ids = self._request_filter_signals(params)
        self.assertEqual([self.signal_no_slo.id], ids)

    def test_filter_on_time(self):
        params = {'punctuality': 'on_time'}

        # Both Signals that have a deadline are on time:
        with freeze_time(self.created_at + timedelta(seconds=60)):
            ids = self._request_filter_signals(params)
        on_time = set([self.signal_slo_w.id, self.signal_slo_c.id])
        self.assertEqual(on_time, set(ids))

        # Signal with SLO in working days is on time (deadline after weekend)
        # the Signal with a SLO in calendar days is late:
        with freeze_time(self.created_at + timedelta(days=1, seconds=60)):
            ids = self._request_filter_signals(params)
        on_time = set([self.signal_slo_w.id])
        self.assertEqual(on_time, set(ids))

    def test_filter_late(self):
        params = {'punctuality': 'late'}

        # Both Signals that have a deadline are on time:
        with freeze_time(self.created_at + timedelta(seconds=60)):
            ids = self._request_filter_signals(params)
        self.assertEqual([], ids)

        # Signal with SLO in working days is on time (deadline after weekend)
        # the Signal with a SLO in calendar days is late:
        with freeze_time(self.created_at + timedelta(days=1, seconds=60)):
            ids = self._request_filter_signals(params)
        late = [self.signal_slo_c.id]
        self.assertEqual(late, ids)

        # Both are late
        with freeze_time(self.created_at + timedelta(days=100)):
            ids = self._request_filter_signals(params)
        late = [self.signal_slo_c.id, self.signal_slo_w.id]
        self.assertEqual(set(late), set(ids))

    def test_filter_late_factor_3(self):
        params = {'punctuality': 'late_factor_3'}

        # Both Signals that have a deadline are on time:
        with freeze_time(self.created_at + timedelta(seconds=60)):
            ids = self._request_filter_signals(params)
        self.assertEqual([], ids)

        # Signal with SLO in working days is on time (deadline after weekend)
        # the Signal with a SLO in calendar days is late:
        with freeze_time(self.created_at + timedelta(days=3, seconds=60)):
            ids = self._request_filter_signals(params)
        late_factor_3 = [self.signal_slo_c.id]
        self.assertEqual(late_factor_3, ids)

        # Both are late
        with freeze_time(self.created_at + timedelta(days=100)):
            ids = self._request_filter_signals(params)
        late = [self.signal_slo_c.id, self.signal_slo_w.id]
        self.assertEqual(set(late), set(ids))
