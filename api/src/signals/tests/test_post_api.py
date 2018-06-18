"""
Test posting / updating to basic endpoints and authorization
"""
import os
import json
# Packages
from rest_framework.test import APITestCase
# from . import factories
from django.conf import settings
from signals.models import Signal
from signals.models import Location
from signals.models import Reporter
from signals.models import Category


class BrowseDatasetsTestCase(APITestCase):
    """
    Test posts op:

    datasets = [
        "signals/signal",
        "signals/status",
        "signals/category",
        "signals/location",
    ]
    """

    fixture_files = {
        "post_signal": "signal_auth_post.json",
        "post_status": "status_post.json",
        "post_category": "category_post.json",
        "post_location": "location_post.json",
    }

    def test_post_signal(self):
        """
        """
        path = os.path.join(
            settings.BASE_DIR,
            'signals',
            'fixtures',
            'signal_auth_post.json'
        )

        with open(path) as fixture_file:
            postjson = json.loads(fixture_file.read())

        url = "/signals/auth/signal/"
        response = self.client.post(url, postjson, format='json')

        self.assertEqual(response.status_code, 201)

        self.assertEqual(Signal.objects.count(), 1)
        s = Signal.objects.all().first()
        self.assertEqual(Reporter.objects.count(), 1)
        r = Reporter.objects.all().first()
        self.assertEqual(r.id, s.reporter.id)

        self.assertEqual(
            Location.objects.filter(signal=s.id).count(), 1)

        self.assertEqual(
            Category.objects.filter(signal=s.id).count(), 1)

    def test_update_signal(self):
        """Update fields? should we allow this?
        """
        pass

    def test_post_status(self):
        """
        """
        pass

    def test_post_location(self):
        """We only create new location items
        """
        pass

    def test_post_category(self):
        """
        """
        pass
