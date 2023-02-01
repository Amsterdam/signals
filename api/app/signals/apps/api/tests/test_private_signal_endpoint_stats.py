import datetime

from django.contrib.auth.models import Permission
from django.utils import timezone
from freezegun import freeze_time

from signals.apps.signals.factories import CategoryFactory, ServiceLevelObjectiveFactory, SignalFactory
from signals.test.utils import SignalsBaseApiTestCase, SIAReadUserMixin


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
