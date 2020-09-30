from django.contrib.gis.geos import Point
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from signals.apps.reporting.models import TDOSignal
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal
from tests.apps.signals.factories import SignalFactory


class TestTDOSignalRepresentation(TestCase):
    def setUp(self):
        self.signal_count = 5
        self.created_at = timezone.now() - timezone.timedelta(days=1)
        self.point_cityhall = Point(52.367640, 4.899527, srid=4326)

        with freeze_time(self.created_at):
            SignalFactory.create_batch(size=self.signal_count, status__state=workflow.GEMELD)

    def test_count(self):
        self.assertEqual(TDOSignal.objects.count(), self.signal_count)

    def test_timestamps(self):
        updated_at = self.created_at + timezone.timedelta(days=1)
        s = Signal.objects.first()

        with freeze_time(updated_at):
            Signal.actions.update_status({'state': workflow.AFGEHANDELD, 'text': 'klaar'}, s)
        s.refresh_from_db()

        e = TDOSignal.objects.get(id=s.id)

        self.assertEqual(s.created_at, e.created_at)
        self.assertEqual(s.updated_at, e.updated_at)

    def test_location(self):
        s = Signal.objects.last()
        Signal.actions.update_location({'geometrie': self.point_cityhall}, s)
        s.refresh_from_db()
        e = TDOSignal.objects.get(id=s.id)

        self.assertEqual(s.location.geometrie, e.geometry)

    def test_status(self):
        s = Signal.objects.first()
        Signal.actions.update_status({'state': workflow.AFGEHANDELD, 'text': 'klaar'}, s)
        s.refresh_from_db()

        e = TDOSignal.objects.get(id=s.id)
        self.assertEqual(s.status.state, e.status)

    def test_slugs(self):
        s = Signal.objects.first()
        e = TDOSignal.objects.get(id=s.id)

        self.assertEqual(s.category_assignment.category.slug, e.sub_slug)
        self.assertEqual(s.category_assignment.category.parent.slug, e.main_slug)
