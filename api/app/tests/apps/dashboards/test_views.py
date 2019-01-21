import json
from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from signals.apps.dashboards.views import DashboardPrototype
from signals.apps.signals.models import CategoryAssignment, Signal, Status, SubCategory
from signals.apps.signals.workflow import AFGEHANDELD, AFWACHTING, BEHANDELING, GEMELD, ON_HOLD
from tests.apps.users.factories import SuperUserFactory


class TestDashboardPrototype(APITestCase):
    url = '/signals/experimental/dashboards/1'
    fixtures = ['categories.json']
    dashboard_prototype = DashboardPrototype()

    report_start = None
    report_end = None

    def _create_test_signal(self, status, subcategory):
        signal = Signal.objects.create(
            text="Test signal",
            incident_date_start=timezone.now()
        )
        status_obj = Status.objects.create(state=status, _signal=signal)
        signal.status = status_obj
        signal.save()

        CategoryAssignment.objects.create(
            _signal=signal,
            sub_category=subcategory
        )

    def setUp(self):
        self._create_test_signal(GEMELD, SubCategory.objects.get(pk=2))
        self._create_test_signal(GEMELD, SubCategory.objects.get(pk=3))
        self._create_test_signal(AFGEHANDELD, SubCategory.objects.get(pk=3))
        self._create_test_signal(AFWACHTING, SubCategory.objects.get(pk=15))
        self._create_test_signal(BEHANDELING, SubCategory.objects.get(pk=56))
        self._create_test_signal(ON_HOLD, SubCategory.objects.get(pk=7))
        self._create_test_signal(AFWACHTING, SubCategory.objects.get(pk=3))
        self._create_test_signal(BEHANDELING, SubCategory.objects.get(pk=38))
        self._create_test_signal(ON_HOLD, SubCategory.objects.get(pk=2))
        self._create_test_signal(GEMELD, SubCategory.objects.get(pk=2))

        # Make sure times correspond with created signals
        self.report_end = (timezone.now() +
                           timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        self.report_start = self.report_end - timedelta(days=1)

    def test_get_signals_per_status(self):
        signals = self.dashboard_prototype._get_signals_per_status(self.report_start,
                                                                   self.report_end)

        # Note that we've not added all statuses in the database.
        result = [
            {"name": "Afgehandeld", "count": 1},
            {"name": "Gemeld", "count": 3},
            {"name": "In afwachting van behandeling", "count": 2},
            {"name": "In behandeling", "count": 2},
            {"name": "On hold", "count": 2},
        ]

        self.assertEquals(result, signals)

        # Test empty interval
        signals = self.dashboard_prototype._get_signals_per_status(
            self.report_end - timedelta(days=1),
            self.report_start,
        )

        result = [
            {"name": "Afgehandeld", "count": 0},
            {"name": "Gemeld", "count": 0},
            {"name": "In afwachting van behandeling", "count": 0},
            {"name": "In behandeling", "count": 0},
            {"name": "On hold", "count": 0},
        ]

        self.assertEquals(result, signals)

    def test_signals_per_category(self):
        signals = self.dashboard_prototype._get_signals_per_category(self.report_start,
                                                                     self.report_end)

        result = [
            {"name": "Afval", "count": 7},
            {"name": "Openbaar groen en water", "count": 0},
            {"name": "Overig", "count": 0},
            {"name": "Overlast Bedrijven en Horeca", "count": 0},
            {"name": "Overlast in de openbare ruimte", "count": 1},
            {"name": "Overlast op het water", "count": 0},
            {"name": "Overlast van dieren", "count": 0},
            {"name": "Overlast van en door personen of groepen", "count": 1},
            {"name": "Wegen, verkeer, straatmeubilair", "count": 1},
        ]

        self.assertEquals(result, signals)

        # Test empty interval
        signals = self.dashboard_prototype._get_signals_per_category(
            self.report_end - timedelta(days=1),
            self.report_start,
        )

        result = [
            {"name": "Afval", "count": 0},
            {"name": "Openbaar groen en water", "count": 0},
            {"name": "Overig", "count": 0},
            {"name": "Overlast Bedrijven en Horeca", "count": 0},
            {"name": "Overlast in de openbare ruimte", "count": 0},
            {"name": "Overlast op het water", "count": 0},
            {"name": "Overlast van dieren", "count": 0},
            {"name": "Overlast van en door personen of groepen", "count": 0},
            {"name": "Wegen, verkeer, straatmeubilair", "count": 0},
        ]

        self.assertEquals(result, signals)

    def test_signals_per_hour(self):
        signals = self.dashboard_prototype._get_signals_per_hour(self.report_start, self.report_end)

        expected_result = []

        start_hour = self.report_end.hour

        hour_list = [i for i in range(start_hour, 24)] + [i for i in range(0, start_hour)]

        for i in hour_list:

            if start_hour <= i <= 23:
                interval_start = self.report_start
            else:
                interval_start = self.report_end

            expected_result.append({
                "interval_start": interval_start.replace(hour=i, tzinfo=None),
                "hour": i,
                "count": 0}
            )

        expected_result[-1]["count"] = 10  # New signals should appear in last hour

        self.assertEquals(expected_result, signals)

        # Test interval without any signals
        for row in expected_result:
            row["interval_start"] = row["interval_start"] - timedelta(days=1)

        expected_result[-1]["count"] = 0

        signals = self.dashboard_prototype._get_signals_per_hour(
            self.report_start - timedelta(days=1),
            self.report_end - timedelta(days=1),
        )

        self.assertEquals(expected_result, signals)

    def test_get_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEquals(401, response.status_code)

    def test_get_authenticated(self):
        superuser = SuperUserFactory.create()
        self.client.force_authenticate(user=superuser)
        response = self.client.get(self.url)
        self.assertEquals(200, response.status_code)

        json_data = json.loads(response.content)

        self.assertEquals(3, len(json_data.keys()))
        self.assertEquals(24, len(json_data["hour"]))
        self.assertEquals(9, len(json_data["category"]))
        self.assertEquals(5, len(json_data["status"]))

        self.assertEquals(10, json_data["hour"][-1]["count"])

        # Test date/time format
        interval_start = (self.report_end - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
        self.assertEquals(interval_start, json_data["hour"][-1]["interval_start"])
        self.assertEquals((self.report_end - timedelta(hours=1)).hour,
                          json_data["hour"][-1]["hour"])

        # Test types
        self.assertTrue(type(json_data["hour"][0]["hour"]) == int)
        self.assertTrue(type(json_data["hour"][0]["count"]) == int)  # 0
        self.assertTrue(type(json_data["hour"][-1]["count"]) == int)  # 10
        self.assertTrue(type(json_data["category"][0]["count"]) == int)  # 7
        self.assertTrue(type(json_data["category"][3]["count"]) == int)  # 0
        self.assertTrue(type(json_data["status"][0]["count"]) == int)
