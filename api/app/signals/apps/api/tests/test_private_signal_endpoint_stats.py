import datetime

from django.contrib.auth.models import Permission

from signals.apps.signals.factories import CategoryFactory, SignalFactory, CategoryAssignmentFactory
from signals.test.utils import SignalsBaseApiTestCase, SIAReadUserMixin


class TestPrivateSignalEndpointStatsTotal(SIAReadUserMixin, SignalsBaseApiTestCase):
    def setUp(self):
        self.sia_read_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_user)

    def test_total_unfiltered(self):
        SignalFactory.create_batch(1000)

        response = self.client.get('/signals/v1/private/signals/stats/total')

        self.assertEqual(200, response.status_code)
        self.assertEqual(1000, response.json()['total'])

    def test_total_filtered_by_category(self):
        category1 = CategoryFactory.create()
        category2 = CategoryFactory.create()
        SignalFactory.create_batch(100, category_assignment__category=category1)
        SignalFactory.create_batch(100, category_assignment__category=category2)

        category_id = category1.pk
        response = self.client.get(f'/signals/v1/private/signals/stats/total?category_id={category_id}')

        self.assertEqual(200, response.status_code)
        self.assertEqual(100, response.json()['total'])

    def test_total_filtered_by_priority(self):
        SignalFactory.create_batch(100, priority__priority='low')
        SignalFactory.create_batch(100, priority__priority='normal')
        SignalFactory.create_batch(100, priority__priority='high')

        response = self.client.get('/signals/v1/private/signals/stats/total?priority=normal')

        self.assertEqual(200, response.status_code)
        self.assertEqual(100, response.json()['total'])
