"""
Test posting / updating to basic endpoints and authorization
"""
import os
import json
# Packages
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
# from . import factories
from django.conf import settings
from signals.models import Signal
from signals.models import Location
from signals.models import Reporter
from signals.models import Category
from signals.models import Status

from . import factories


class PostTestCase(APITestCase):
    """
    Test posts op:

    datasets = [
        "signals/signal",
        "signals/status",
        "signals/category",
        "signals/location",
    ]

    TODO ADD AUTHENTICATION
    """

    fixture_files = {
        "post_signal": "signal_auth_post.json",
        "post_status": "status_auth_post.json",
        "post_category": "category_post.json",
        "post_location": "location_post.json",
    }

    def _get_fixture(self, name):

        filename = self.fixture_files[name]
        path = os.path.join(
            settings.BASE_DIR,
            'signals',
            'fixtures',
            filename
        )

        with open(path) as fixture_file:
            postjson = json.loads(fixture_file.read())

        return postjson

    def setUp(self):
        self.s = factories.SignalFactory()

        self.loc = factories.LocationFactory(_signal=self.s)
        self.status = factories.StatusFactory(_signal=self.s)
        self.c = factories.CategoryFactory(_signal=self.s)
        self.reporter = factories.ReporterFactory(_signal=self.s)

        self.status.signal.add(self.s),
        self.loc.signal.add(self.s)
        self.c.signal.add(self.s)
        self.reporter.signal.add(self.s)

    def test_post_signal(self):
        """Post een compleet signaal.
        """

        url = "/signals/auth/signal/"
        postjson = self._get_fixture('post_signal')
        response = self.client.post(url, postjson, format='json')

        self.assertEqual(response.status_code, 201)

        self.assertEqual(Signal.objects.count(), 2)
        s = Signal.objects.all().first()
        self.assertEqual(Reporter.objects.count(), 2)
        r = Reporter.objects.all().first()
        self.assertEqual(r.id, s.reporter.id)

        self.assertEqual(
            Location.objects.filter(signal=s.id).count(), 1)

        self.assertEqual(
            Category.objects.filter(signal=s.id).count(), 1)

        self.assertEqual(
            Status.objects.filter(signal=s.id).count(), 1)

        self.assertEqual(
            Category.objects.filter(signal=s.id).first()._signal.id, s.id,
            "Category is missing _signal field?"
        )

        self.assertEqual(
            Status.objects.filter(signal=s.id).first()._signal.id, s.id,
            "State is missing _signal field?"
        )

        self.assertEqual(
            Reporter.objects.filter(signal=s.id).first()._signal.id, s.id,
            "Reporter is missing _signal field?"
        )

    def test_post_status(self):
        """Update status of signal

        - Add a status object with link to Signal
        - Change signal object status field.

        """
        url = "/signals/auth/status/"
        postjson = self._get_fixture('post_status')
        signal_url = reverse('signal-detail', args=[self.s.id])
        postjson['_signal'] = signal_url
        response = self.client.post(url, postjson, format='json')
        result = response.json()
        self.assertEqual(response.status_code, 201)
        self.s.refresh_from_db()
        self.assertEqual(self.s.status.id, result['id'])

    def test_post_location(self):
        """We only create new location items
        """
        pass

    def test_post_category(self):
        """
        """
        pass
