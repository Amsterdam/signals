from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from signals import API_VERSIONS
from signals.apps.signals import workflow
from signals.apps.signals.models import History, MainCategory, Signal
from signals.utils.version import get_version
from tests.apps.signals.factories import (
    MainCategoryFactory,
    NoteFactory,
    SignalFactory,
    SubCategoryFactory
)
from tests.apps.users.factories import SuperUserFactory, UserFactory


class TestAPIRoot(APITestCase):

    def test_http_header_api_version(self):
        response = self.client.get('/signals/v1/')

        self.assertEqual(response['X-API-Version'], get_version(API_VERSIONS['v1']))


class TestCategoryTermsEndpoints(APITestCase):
    fixtures = ['categories.json', ]

    def test_category_list(self):
        # Asserting that we've 9 `MainCategory` objects loaded from the json fixture.
        self.assertEqual(MainCategory.objects.count(), 9)

        url = '/signals/v1/public/terms/categories/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data['results']), 9)

    def test_category_detail(self):
        # Asserting that we've 13 sub categories for our main category "Afval".
        main_category = MainCategoryFactory.create(name='Afval')
        self.assertEqual(main_category.sub_categories.count(), 13)

        url = '/signals/v1/public/terms/categories/{slug}'.format(slug=main_category.slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['name'], 'Afval')
        self.assertEqual(len(data['sub_categories']), 13)

    def test_sub_category_detail(self):
        sub_category = SubCategoryFactory.create(name='Grofvuil', main_category__name='Afval')

        url = '/signals/v1/public/terms/categories/{slug}/sub_categories/{sub_slug}'.format(
            slug=sub_category.main_category.slug,
            sub_slug=sub_category.slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['name'], 'Grofvuil')
        self.assertIn('is_active', data)


class TestPrivateEndpoints(APITestCase):
    """Test whether the endpoints in V1 API """
    endpoints = [
        '/signals/v1/private/signals/',
    ]

    def setUp(self):
        self.signal = SignalFactory(
            id=1,
            location__id=1,
            status__id=1,
            category_assignment__id=1,
            reporter__id=1,
            priority__id=1
        )

        # Forcing authentication
        user = UserFactory.create()  # Normal user without any extra permissions.
        self.client.force_authenticate(user=user)

        # Add one note to the signal
        self.note = NoteFactory(id=1, _signal=self.signal)

    def test_basics(self):
        self.assertEqual(Signal.objects.count(), 1)
        s = Signal.objects.get(pk=1)
        self.assertIsInstance(s, Signal)

    def test_get_lists(self):
        for url in self.endpoints:
            response = self.client.get(url)

            self.assertEqual(response.status_code, 200, 'Wrong response code for {}'.format(url))
            self.assertEqual(response['Content-Type'],
                             'application/json',
                             'Wrong Content-Type for {}'.format(url))
            self.assertIn('count', response.data, 'No count attribute in {}'.format(url))

    def test_get_lists_html(self):
        for url in self.endpoints:
            response = self.client.get('{}?format=api'.format(url))

            self.assertEqual(response.status_code, 200, 'Wrong response code for {}'.format(url))
            self.assertEqual(response['Content-Type'],
                             'text/html; charset=utf-8',
                             'Wrong Content-Type for {}'.format(url))
            self.assertIn('count', response.data, 'No count attribute in {}'.format(url))

    def test_get_detail(self):
        for endpoint in self.endpoints:
            url = f'{endpoint}1'
            response = self.client.get(url)

            self.assertEqual(response.status_code, 200, 'Wrong response code for {}'.format(url))

    def test_delete_not_allowed(self):
        for endpoint in self.endpoints:
            url = f'{endpoint}1'
            response = self.client.delete(url)

            self.assertEqual(response.status_code, 405, 'Wrong response code for {}'.format(url))

    def test_put_not_allowed(self):
        for endpoint in self.endpoints:
            url = f'{endpoint}1'
            response = self.client.put(url)

            self.assertEqual(response.status_code, 405, 'Wrong response code for {}'.format(url))

    def test_patch_not_allowed(self):
        for endpoint in self.endpoints:
            url = f'{endpoint}1'
            response = self.client.patch(url)

            self.assertEqual(response.status_code, 405, 'Wrong response code for {}'.format(url))


class TestHistoryAction(APITestCase):
    def setUp(self):
        self.signal = SignalFactory.create()
        self.superuser = SuperUserFactory(username='superuser@example.com')
        self.user = UserFactory(username='user@example.com')

    def test_history_action_present(self):
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 401)

        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

    def test_history_endpoint_rendering(self):
        history_entries = History.objects.filter(_signal__id=self.signal.pk)

        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

        result = response.json()
        self.assertEqual(len(result), history_entries.count())

    def test_history_entry_contents(self):
        keys = ['identifier', 'when', 'what', 'action', 'description', 'who', '_signal']

        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)

        for entry in response.json():
            for k in keys:
                self.assertIn(k, entry)

    def test_update_shows_up(self):
        # Get a baseline for the Signal history
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        n_entries = len(response.json())
        self.assertEqual(response.status_code, 200)

        # Update the Signal status, and ...
        status = Signal.actions.update_status(
            {
                'text': 'DIT IS EEN TEST',
                'state': workflow.AFGEHANDELD,
                'user': self.user,
            },
            self.signal
        )

        # ... check that the new status shows up as most recent entry in history.
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.id}/history')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), n_entries + 1)

        new_entry = response.json()[0]  # most recent status should be first
        self.assertEqual(new_entry['who'], self.user.username)
        self.assertEqual(new_entry['description'], status.text)


class TestImageUpload(APITestCase):
    def setUp(self):
        self.signal = SignalFactory.create()
        self.superuser = SuperUserFactory(username='superuser@example.com')

        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )

    def test_authenticated_upload(self):
        # images are attached to pre-existing Signals
        endpoint = f'/signals/v1/private/signals/{self.signal.id}/upload_image'
        image = SimpleUploadedFile('image.gif', self.small_gif, content_type='image/gif')

        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(
            endpoint,
            data={'image': image},
            # format='multipart'
        )

        self.assertEqual(response.status_code, 202)
