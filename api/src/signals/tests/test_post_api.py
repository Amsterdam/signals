"""
Test posting / updating to basic endpoints and authorization
"""
import os
import json

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from signals.models import Signal
from signals.models import Location
from signals.models import Reporter
from signals.models import Category
from signals.models import Status
from signals.tests import factories


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
        "post_signal": "signal_post.json",
        "post_status": "status_auth_post.json",
        "post_category": "category_auth_post.json",
        "post_location": "location_auth_post.json",
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
        self.signal = factories.SignalFactory()
        self.location = self.signal.location
        self.status = self.signal.status
        self.category = self.signal.category
        self.reporter = self.signal.reporter

        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )

    def test_post_signal(self):
        """Post een compleet signaal."""
        url = "/signals/signal/"
        postjson = self._get_fixture('post_signal')
        response = self.client.post(url, postjson, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Signal.objects.count(), 2)
        id = response.data['id']
        s = Signal.objects.get(id=id)

        self.assertEqual(Reporter.objects.count(), 2)
        lr = Reporter.objects.filter(signal=s.id)
        self.assertEqual(lr.count(), 1)
        r = lr[0]

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

        self.assertEqual(
            Category.objects.filter(signal=s.id).first().department, "CCA,ASC,STW"
        )

    def test_post_signal_image(self):
        url = '/signals/signal/image/'
        image = SimpleUploadedFile(
            'image.gif', self.small_gif, content_type='image/gif')
        response = self.client.post(
            url, {'signal_id': self.signal.id, 'image': image})

        self.assertEqual(response.status_code, 202)
        self.signal.refresh_from_db()
        self.assertTrue(self.signal.image)

    def test_post_signal_image_already_exists(self):
        self.signal.image = 'already_exists'
        self.signal.save()

        url = '/signals/signal/image/'
        image = SimpleUploadedFile(
            'image.gif', self.small_gif, content_type='image/gif')
        response = self.client.post(
            url, {'signal_id': self.signal.id, 'image': image})

        self.assertEqual(response.status_code, 403)

    def test_post_status(self):
        """Update status of signal

        - Add a status object with link to Signal
        - Change signal object status field.

        """
        url = "/signals/auth/status/"
        postjson = self._get_fixture('post_status')
        postjson['_signal'] = self.signal.id
        response = self.client.post(url, postjson, format='json')
        result = response.json()
        self.assertEqual(response.status_code, 201)
        self.signal.refresh_from_db()
        # check that current status of signal is now this one
        self.assertEqual(self.signal.status.id, result['id'])

    def test_post_location(self):
        """We only create new location items"""
        url = "/signals/auth/location/"
        postjson = self._get_fixture('post_location')
        postjson['_signal'] = self.signal.id
        response = self.client.post(url, postjson, format='json')
        result = response.json()
        self.assertEqual(response.status_code, 201)
        self.signal.refresh_from_db()
        # check that current location of signal is now this one
        self.assertEqual(self.signal.location.id, result['id'])

    def test_post_category(self):
        """Category Post"""
        url = "/signals/auth/category/"
        postjson = self._get_fixture('post_category')
        postjson['_signal'] = self.signal.id
        response = self.client.post(url, postjson, format='json')
        result = response.json()
        self.assertEqual(response.status_code, 201)
        self.signal.refresh_from_db()
        # check that current location of signal is now this one
        self.assertEqual(self.signal.category.id, result['id'])
        self.assertEqual(self.signal.category.department, "CCA,ASC,WAT")
