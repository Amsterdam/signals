from datetime import datetime, timedelta
from random import shuffle

from django.utils import timezone
from freezegun import freeze_time

from signals.apps.signals.models import Priority
from signals.apps.signals.workflow import BEHANDELING, GEMELD, ON_HOLD
from tests.apps.feedback.factories import FeedbackFactory
from tests.apps.signals.factories import (
    CategoryAssignmentFactory,
    CategoryFactory,
    NoteFactory,
    ParentCategoryFactory,
    SignalFactory,
    StatusFactory,
    TypeFactory
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
                    TypeFactory.create(_signal=signal, name=type_code)
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
