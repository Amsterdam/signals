import json
import os
from unittest import mock, skip
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import include, path

from signals import API_VERSIONS
from signals.apps.api.urls import signal_router_v0
from signals.apps.signals import workflow
from signals.apps.signals.models import (
    STADSDEEL_CENTRUM,
    STADSDEEL_OOST,
    Category,
    CategoryAssignment,
    Location,
    Note,
    Priority,
    Reporter,
    Signal,
    Status
)
from signals.apps.signals.models.category_translation import CategoryTranslation
from signals.utils.version import get_version
from tests.apps.signals import factories
from tests.apps.signals.attachment_helpers import (
    add_image_attachments,
    add_non_image_attachments,
    small_gif
)
from tests.apps.signals.factories import CategoryFactory, SignalFactoryWithImage
from tests.apps.users.factories import UserFactory
from tests.test import SignalsBaseApiTestCase, SuperUserMixin


# V0 has been disabled but we still want to test the code, so for the tests we will add the endpoints
class NameSpace:
    pass


test_urlconf = NameSpace()
test_urlconf.urlpatterns = [
    path('signals/', include([
        path('', include((signal_router_v0.urls, 'signals'), namespace='v0')),
        path('', include(('signals.apps.api.v1.urls', 'signals'), namespace='v1')),
    ])),
]


@override_settings(ROOT_URLCONF=test_urlconf)
class TestAPIRoot(SignalsBaseApiTestCase):

    def test_signals_index(self):
        response = self.client.get('/signals/')

        expected_api_version_1 = {
            '_links': {
                'self': {
                    'href': 'http://testserver/signals/v1/',
                }
            },
            'version': get_version(API_VERSIONS['v1']),
            'status': 'in development',
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['v1'], expected_api_version_1)

    def test_http_header_api_version(self):
        response = self.client.get('/signals/')

        self.assertEqual(response['X-API-Version'], get_version(API_VERSIONS['v0']))


@override_settings(ROOT_URLCONF=test_urlconf)
class TestAuthAPIEndpoints(SignalsBaseApiTestCase):
    endpoints = [
        '/signals/auth/signal/',
        '/signals/auth/status/',
        '/signals/auth/category/',
        '/signals/auth/location/',
        '/signals/auth/priority/',
        '/signals/auth/note/',
    ]

    def setUp(self):
        self.signal = factories.SignalFactory(id=1,
                                              location__id=1,
                                              status__id=1,
                                              category_assignment__id=1,
                                              reporter__id=1,
                                              priority__id=1)

        # Forcing authentication
        self.client.force_authenticate(user=self.user)

        # Add one note to the signal
        self.note = factories.NoteFactory(id=1, _signal=self.signal)

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
            url = f'{endpoint}1/'
            response = self.client.get(url)

            self.assertEqual(response.status_code, 200, 'Wrong response code for {}'.format(url))

    def test_delete_not_allowed(self):
        for endpoint in self.endpoints:
            url = f'{endpoint}1/'
            response = self.client.delete(url)

            self.assertEqual(response.status_code, 405, 'Wrong response code for {}'.format(url))

    def test_put_not_allowed(self):
        for endpoint in self.endpoints:
            url = f'{endpoint}1/'
            response = self.client.put(url)

            self.assertEqual(response.status_code, 405, 'Wrong response code for {}'.format(url))

    def test_patch_not_allowed(self):
        for endpoint in self.endpoints:
            url = f'{endpoint}1/'
            response = self.client.patch(url)

            self.assertEqual(response.status_code, 405, 'Wrong response code for {}'.format(url))


@override_settings(ROOT_URLCONF=test_urlconf)
class TestAPIEndpointsBase(SignalsBaseApiTestCase):
    fixture_files = {
        "post_signal": "signal_post.json",
        "post_status": "status_auth_post.json",
        "post_category": "category_auth_post.json",
        "post_location": "location_auth_post.json",
    }  # Custom fixture files
    fixtures = ['categories.json', ]  # Django initial data

    def _get_fixture(self, name):
        filename = self.fixture_files[name]
        path = os.path.join(os.path.dirname(__file__), 'request_data', filename)

        with open(path) as fixture_file:
            postjson = json.loads(fixture_file.read())

        return postjson

    def setUp(self):
        self.signal = factories.SignalFactory.create()
        self.location = self.signal.location
        self.status = self.signal.status
        self.category_assignment = self.signal.category_assignment
        self.reporter = self.signal.reporter


@override_settings(ROOT_URLCONF=test_urlconf)
class TestPublicSignalEndpoint(TestAPIEndpointsBase):
    """Test for public endpoint `/signals/signal/`."""

    endpoint = '/signals/signal/'

    def test_get_detail(self):
        """Signal detail endpoint should only return the `Status` of the given `Signal`."""
        response = self.client.get(f'{self.endpoint}{self.signal.signal_id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('signal_id'), str(self.signal.signal_id))
        self.assertEqual(response.data.get('status').get('id'), self.signal.status.id)
        self.assertEqual(response.data.get('status').get('state'), str(self.signal.status.state))
        self.assertEqual(response.data.get('text'), None)
        self.assertEqual(response.data.get('category'), None)
        self.assertEqual(response.data.get('location'), None)
        self.assertEqual(response.data.get('reporter'), None)
        self.assertEqual(response.data.get('priority'), None)
        self.assertEqual(response.data.get('id'), None)

    def test_get_list(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, 405)

    def test_delete_not_allowed(self):
        response = self.client.delete(f'{self.endpoint}1/')

        self.assertEqual(response.status_code, 405)

    def test_put_not_allowed(self):
        response = self.client.put(f'{self.endpoint}1/')

        self.assertEqual(response.status_code, 405)

    def test_patch_not_allowed(self):
        response = self.client.patch(f'{self.endpoint}1/')

        self.assertEqual(response.status_code, 405)

    def test_post_signal_with_json(self):
        postjson = self._get_fixture('post_signal')
        postjson['source'] = 'online'

        response = self.client.post(self.endpoint, postjson, format='json')
        self.assertEqual(response.status_code, 201)

        self.assertTrue('image' in response.json())
        self.assertFalse('attachments' in response.json(), 'Attachments is a v1-only field')

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
            CategoryAssignment.objects.filter(signal=s.id).count(), 1)

        self.assertEqual(
            Status.objects.filter(signal=s.id).count(), 1)

        self.assertEqual(
            CategoryAssignment.objects.filter(signal=s.id).first()._signal.id, s.id,
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

    @skip('SIG-1570 cannot be deployed yet - extra validation disabled')
    def test_post_signal_with_json_anonymous_invalid_source(self):
        postjson = self._get_fixture('post_signal')
        postjson['source'] = 'invalid-source'

        self.client.logout()

        response = self.client.post(self.endpoint, postjson, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['source'][0], 'Invalid source given for anonymous user')

    @patch("signals.apps.api.v1.validation.address.base.BaseAddressValidation.validate_address")
    def test_post_signal_with_bag_validated(self, validate_address):
        """ Tests that the bag_validated field cannot be set manually and that the address
            validation is NOT called on the v0 endpoint """

        postjson = self._get_fixture('post_signal')
        postjson["location"]["bag_validated"] = True

        response = self.client.post(self.endpoint, postjson, format='json')
        self.assertEqual(response.status_code, 201)

        validate_address.assert_not_called()

        id = response.data['id']
        s = Signal.objects.get(id=id)
        self.assertFalse(s.location.bag_validated)

    def test_post_signal_with_multipart_and_image(self):
        data = self._get_fixture('post_signal')

        # Adding a testing image to the posting data.
        image = SimpleUploadedFile(
            'image.gif', small_gif, content_type='image/gif')
        data['image'] = image

        # Changing data dict structure (loaded from json file) to work with
        # multipart structure.
        for key, value in data['status'].items():
            data['status.{}'.format(key)] = value
        for key, value in data['location'].items():
            data['location.{}'.format(key)] = value
        data['location.geometrie'] = 'POINT (4.893697 52.372840)'
        for key, value in data['category'].items():
            data['category.{}'.format(key)] = value
        for key, value in data['reporter'].items():
            data['reporter.{}'.format(key)] = value

        del data['status']
        del data['status.extra_properties']
        del data['location']
        del data['location.address']
        del data['location.extra_properties']
        del data['category']
        del data['reporter']
        del data['incident_date_end']
        del data['operational_date']
        del data['updated_at']
        del data['upload']

        response = self.client.post(self.endpoint, data)

        self.assertEqual(response.status_code, 201)

        signal = Signal.objects.get(id=response.json()['id'])
        self.assertTrue(signal.image)
        self.assertEqual("http://testserver" + signal.image_crop.url, response.json()['image'])

    def test_post_signal_image(self):
        url = f'{self.endpoint}image/'
        image = SimpleUploadedFile(
            'image.gif', small_gif, content_type='image/gif')
        response = self.client.post(
            url, {'signal_id': self.signal.signal_id, 'image': image})

        self.assertEqual(response.status_code, 202)
        self.signal.refresh_from_db()
        self.assertTrue(self.signal.image)

    def test_post_signal_image_other_attachments_exists(self):
        """ It should be possible to add an image when no image is added to the signal, even if
        other types of attachments are added. """
        add_non_image_attachments(self.signal)

        url = f'{self.endpoint}image/'
        image = SimpleUploadedFile(
            'image.gif', small_gif, content_type='image/gif')
        response = self.client.post(
            url, {'signal_id': self.signal.signal_id, 'image': image})

        self.assertEqual(response.status_code, 202)
        self.signal.refresh_from_db()
        self.assertTrue(self.signal.image)

    def test_post_signal_image_image_attachment_exists(self):
        """ It should not be possible to add an image through the v0 api when one of the already
        present attachments is an image """

        # Add some non-image attachments
        add_non_image_attachments(self.signal)

        # Add image attachment
        add_image_attachments(self.signal, 1)

        image2 = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')

        # Then assert that adding another image through the v0 API fails
        url = f'{self.endpoint}image/'
        response = self.client.post(
            url, {'signal_id': self.signal.signal_id, 'image': image2})

        # 403 is not the best response code, but consistent with existing v0 endpoint
        self.assertEqual(response.status_code, 403)
        self.signal.refresh_from_db()
        self.assertTrue(self.signal.image)


@override_settings(ROOT_URLCONF=test_urlconf)
class TestAuthSignalEndpoint(SignalsBaseApiTestCase):

    def setUp(self):
        self.first = factories.SignalFactory.create(location__stadsdeel=STADSDEEL_OOST)
        self.high_priority = factories.SignalFactory.create(
            priority__priority=Priority.PRIORITY_HIGH,
            location__stadsdeel=STADSDEEL_OOST)
        self.centrum = factories.SignalFactory.create(location__stadsdeel=STADSDEEL_CENTRUM)
        self.last = factories.SignalFactory.create(location__stadsdeel=STADSDEEL_OOST)

        # Forcing authentication
        self.client.force_authenticate(user=self.superuser)

    def test_ordering_by_all_fields(self):
        # Just check if all ordering fields are working as in, do they return a 200 response.
        ordering_fields = [
            'id',
            'created_at',
            'updated_at',
            'stadsdeel',
            'sub_category',
            'main_category',
            'status',
            'priority',
            'address',
        ]
        for field in ordering_fields:
            response = self.client.get(f'/signals/auth/signal/?ordering={field}')
            self.assertEqual(response.status_code, 200, f'Ordering by `{field}` did not return 200')

    def test_ordering_by_created_at_asc(self):
        response = self.client.get('/signals/auth/signal/?ordering=created_at')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['results'][0]['signal_id'], str(self.first.signal_id))
        self.assertEqual(data['results'][3]['signal_id'], str(self.last.signal_id))

    def test_ordering_by_created_at_desc(self):
        response = self.client.get('/signals/auth/signal/?ordering=-created_at')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['results'][0]['signal_id'], str(self.last.signal_id))
        self.assertEqual(data['results'][3]['signal_id'], str(self.first.signal_id))

    def test_ordering_by_priority_asc(self):
        response = self.client.get('/signals/auth/signal/?ordering=priority')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['results'][0]['signal_id'], str(self.high_priority.signal_id))

    def test_ordering_by_location_stadsdeel_asc(self):
        response = self.client.get('/signals/auth/signal/?ordering=stadsdeel')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['results'][0]['signal_id'], str(self.centrum.signal_id))

    def test_return_first_image_attachment(self):
        """ If multiple attachments are present, the v0 API should return only the first ever
        uploaded image through the 'image' field and ignore the rest. """

        # Create some random attachments, keep the first
        add_non_image_attachments(self.last)
        image_attachment, _ = add_image_attachments(self.last, 2)
        add_non_image_attachments(self.last)
        add_image_attachments(self.last, 3)

        url = "/signals/auth/signal/{}/".format(self.last.id)
        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        json_resp = response.json()

        self.assertEqual("http://testserver" + image_attachment.image_crop.url, json_resp["image"])
        self.assertFalse('attachments' in json_resp, "Attachments is a v1-only field")


@override_settings(ROOT_URLCONF=test_urlconf)
class TestAuthAPIEndpointsPOST(TestAPIEndpointsBase):

    def setUp(self):
        super().setUp()

        # Forcing authentication (Superuser has all permissions by default.)
        self.client.force_authenticate(user=self.superuser)

    def test_signal_post_not_allowed(self):
        endpoint = '/signals/auth/signal/'
        response = self.client.post(endpoint, {}, format='json')

        self.assertEqual(response.status_code, 405)

    def test_endpoints_forbidden(self):
        self.client.force_authenticate(user=self.user)

        # These endpoints are protected with object-level permissions. Check if we can't POST to
        # these endpoints with a normal `User` instance.
        endpoints = [
            '/signals/auth/status/',
            '/signals/auth/category/',
            '/signals/auth/location/',
            '/signals/auth/priority/',
        ]
        for endpoint in endpoints:
            response = self.client.post(endpoint, {}, format='json')
            self.assertEqual(response.status_code,
                             403,
                             'Wrong response code for {}'.format(endpoint))

    def test_post_status_all_fields(self):
        # Asserting initial state.
        self.assertEqual(self.signal.status.state, workflow.GEMELD)

        # Posting a new status change.
        url = '/signals/auth/status/'
        data = {
            '_signal': self.signal.id,
            'text': 'Changing status to "afwachting"',
            'user': 'user@example.com',
            'target_api': None,
            'state': workflow.AFWACHTING,
            'extra_properties': {},
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)

        result = response.json()
        self.signal.refresh_from_db()
        self.assertEqual(self.signal.status.text, result['text'])
        self.assertEqual(self.signal.status.user, result['user'])
        self.assertEqual(self.signal.status.state, result['state'])
        self.assertEqual(self.signal.status.user, self.superuser.username)

    def test_post_status_minimal_fiels(self):
        # Asserting initial state.
        self.assertEqual(self.signal.status.state, workflow.GEMELD)

        # Posting a new status change.
        url = '/signals/auth/status/'
        data = {
            '_signal': self.signal.id,
            'state': workflow.AFWACHTING,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)

        self.signal.refresh_from_db()
        result = response.json()
        self.assertEqual(self.signal.status.state, result['state'])
        self.assertEqual(self.signal.status.user, self.superuser.username)

    @skip('This transition became valid because re-categorization and status change to GEMELD')
    def test_post_status_invalid_transition(self):
        # Prepare current state.
        self.signal.status.state = workflow.AFWACHTING
        self.signal.status.save()

        # Post an unallowed status change from the API.
        url = '/signals/auth/status/'
        data = {
            '_signal': self.signal.id,
            'state': workflow.GEMELD,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 400)

        result = response.json()
        self.assertIn('state', result.keys())

    def test_post_status_missing_target_api(self):
        # Post an status change with a missing `target_api` which is required.
        url = '/signals/auth/status/'
        data = {
            '_signal': self.signal.id,
            'state': workflow.TE_VERZENDEN,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 400)

        result = response.json()
        self.assertIn('target_api', result.keys())

    def test_post_status_push_to_sigmax_permission_denied(self):
        status_content_type = ContentType.objects.get_for_model(Status)
        permission_add_status, _ = Permission.objects.get_or_create(
            codename='add_status',
            content_type=status_content_type)
        user = UserFactory.create()
        user.user_permissions.add(permission_add_status)
        self.client.force_authenticate(user=user)

        # Post an status change "push to Sigmax" without the correct permissions.
        url = '/signals/auth/status/'
        data = {
            '_signal': self.signal.id,
            'state': workflow.TE_VERZENDEN,
            'target_api': Status.TARGET_API_SIGMAX,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 403)

        result = response.json()
        self.assertIn('state', result.keys())

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
        self.assertEqual(self.signal.location.created_by, self.superuser.username)

    def test_post_category(self):
        category_name = 'Overlast op het water - snel varen'
        category = CategoryFactory.create(name=category_name,
                                          parent__name='Overlast op het water')

        # Asserting that we don't change the category to the same value the signal object
        # already has.
        self.assertNotEqual(self.signal.category_assignment.category.name, category_name)

        url = '/signals/auth/category/'
        postjson = {
            '_signal': self.signal.id,
            'sub_category': '/signals/v1/public/terms/categories/{}/sub_categories/{}'.format(
                category.parent.slug, category.slug),
        }
        response = self.client.post(url, postjson, format='json')
        self.assertEqual(response.status_code, 201)

        result = response.json()
        self.assertEqual(result['sub'], category_name)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.category_assignment.category, category)
        self.assertEqual(self.signal.category_assignment.created_by, self.superuser.username)

    def test_post_category_backwards_compatibility_style(self):
        """
        Note, this is a backwards compatibility test for changing the category "old-style" posting.
        Implementation and test should be removed after the FE is updated to "new-style" of changing
        categories.
        """
        category_name = 'Overlast op het water - snel varen'
        CategoryFactory.create(name=category_name,
                               parent__name='Overlast op het water')

        # Asserting that we don't change the category to the same value the signal object
        # already has.
        self.assertNotEqual(self.signal.category_assignment.category.name, category_name)

        url = '/signals/auth/category/'
        postjson = {
            '_signal': self.signal.id,
            'main': 'Overlast op het water',
            'sub': category_name,
        }
        response = self.client.post(url, postjson, format='json')
        self.assertEqual(response.status_code, 201)

        result = response.json()
        self.assertEqual(result['sub'], category_name)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.category_assignment.category.name, category_name)
        self.assertEqual(self.signal.category_assignment.created_by, self.superuser.username)

    def test_post_priority(self):
        url = '/signals/auth/priority/'
        data = {
            '_signal': self.signal.id,
            'priority': Priority.PRIORITY_HIGH,
        }
        response = self.client.post(url, data, format='json')
        result = response.json()

        self.assertEqual(response.status_code, 201)

        self.signal.refresh_from_db()
        self.assertEqual(self.signal.priority.id, result['id'])
        self.assertEqual(self.signal.priority.priority, Priority.PRIORITY_HIGH)
        self.assertEqual(self.signal.priority.created_by, self.superuser.username)

    def test_post_note(self):
        url = '/signals/auth/note/'
        data = {
            '_signal': self.signal.id,
            'text': 'Dit is een test notitie bij een test melding.',

        }
        self.assertEqual(Note.objects.count(), 0)
        response = self.client.post(url, data, format='json')
        result = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Note.objects.count(), 1)

        self.signal.refresh_from_db()
        self.assertEqual(self.signal.notes.count(), 1)
        for field in ['_links', 'text', 'created_at', 'created_by', '_signal']:
            self.assertIn(field, result)

        note = Note.objects.get(_signal=self.signal)
        self.assertEqual(note.created_by, self.superuser.username)

    def test_update_category_assignment_to_the_same_category(self):
        url = '/signals/auth/category/'
        category = self.signal.category_assignment.category
        data = {
            '_signal': self.signal.id,
            'sub_category': '/signals/v1/public/terms/categories/{}/sub_categories/{}'.format(
                category.parent.slug,
                category.slug
            )
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn('non_field_errors', data)
        self.assertIn('Cannot assign the same category twice', data['non_field_errors'])


@override_settings(ROOT_URLCONF=test_urlconf)
class TestUserLogging(TestAPIEndpointsBase):
    """Check that the API returns who did what and when."""

    def setUp(self):
        super().setUp()

        # Forcing authentication (Superuser has all permissions by default.)
        self.client.force_authenticate(user=self.superuser)

        # We want the following fields present in relevant authenticated endpoints.
        self.required_fields = ['created_at', 'created_by', '_signal']

    def test_category_assignment_is_logged(self):
        self.signal.category_assignment.created_by = 'veelmelder@example.com'
        self.signal.category_assignment.save()

        pk = self.signal.category_assignment.pk
        response = self.client.get('/signals/auth/category/{}/'.format(pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CategoryAssignment.objects.count(), 1)

        result = response.json()
        for field in self.required_fields:
            self.assertIn(field, result)
            self.assertNotEqual(result[field], None)

        self.assertEqual(self.signal.category_assignment.created_by, result['created_by'])

    def test_location_is_logged(self):
        self.signal.location.created_by = 'veelmelder@example.com'
        self.signal.location.save()

        pk = self.signal.location.pk
        response = self.client.get('/signals/auth/location/{}/'.format(pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Location.objects.count(), 1)

        result = response.json()
        for field in self.required_fields:
            self.assertIn(field, result)
            self.assertNotEqual(result[field], None)

        self.assertEqual(self.signal.location.created_by, result['created_by'])

    def test_priority_is_logged(self):
        self.signal.priority.created_by = 'veelmelder@example.com'
        self.signal.priority.save()

        pk = self.signal.priority.pk
        response = self.client.get('/signals/auth/priority/{}/'.format(pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Priority.objects.count(), 1)

        result = response.json()
        for field in self.required_fields:
            self.assertIn(field, result)
            self.assertNotEqual(result[field], None)

        self.assertEqual(self.signal.priority.created_by, result['created_by'])

    def test_status_is_logged(self):
        # Note: for backwards compatibility we did not rename `user` to `created_by`.
        self.signal.status.user = 'veelmelder@example.com'
        self.signal.status.save()

        pk = self.signal.status.pk
        response = self.client.get('/signals/auth/status/{}/'.format(pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Status.objects.count(), 1)

        result = response.json()
        for field in ['created_at', 'user', '_signal']:
            self.assertIn(field, result)
            self.assertNotEqual(result[field], None)

        self.assertEqual(self.signal.status.user, result['user'])

    def test_note_is_logged(self):
        note = Note.objects.create(
            _signal=self.signal,
            text='Notitie tekst',
            created_by='veelmelder@example.com',
        )
        note.save()
        note.refresh_from_db()

        pk = note.pk
        response = self.client.get('/signals/auth/note/{}/'.format(pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Note.objects.count(), 1)

        result = response.json()
        for field in self.required_fields:
            self.assertIn(field, result)
            self.assertNotEqual(result[field], None)

        self.assertEqual(note.created_by, result['created_by'])


@override_settings(ROOT_URLCONF=test_urlconf)
class TestNoImageUrlsInSignalList(TestAPIEndpointsBase, SuperUserMixin):
    """We do not want the image urls generated on list endpoints"""

    def setUp(self):
        self.signal_list_endpoint = '/signals/auth/signal/'
        self.signal_with_image = SignalFactoryWithImage.create()

    def test_list_endpoint_no_image_url(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get(self.signal_list_endpoint)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['count'], 1)
        self.assertNotIn('image', response_data['results'][0])


@override_settings(ROOT_URLCONF=test_urlconf)
class TestMlPredictCategory(SignalsBaseApiTestCase):
    test_host = 'http://testserver'
    endpoint = '/signals/category/prediction'

    def setUp(self):
        self.test_parentcategory_overig = Category.objects.get(
            slug='overig',
            parent__isnull=True,
        )
        self.test_subcategory_overig = Category.objects.get(
            parent=self.test_parentcategory_overig,
            slug='overig',
            parent__isnull=False,
        )
        self.link_test_subcategory_overig = '/signals/v1/public/terms/categories/{}/sub_categories/{}'.format(  # noqa
            self.test_host,
            self.test_subcategory_overig.parent.slug,
            self.test_subcategory_overig.slug,
        )

        self.test_subcategory = CategoryFactory.create()
        self.link_test_subcategory = '{}/signals/v1/public/terms/categories/{}/sub_categories/{}'.format(  # noqa
            self.test_host,
            self.test_subcategory.parent.slug,
            self.test_subcategory.slug,
        )

        self.test_subcategory_translated = CategoryFactory.create(is_active=False)
        self.link_test_subcategory_translated = '{}/signals/v1/public/terms/categories/{}/sub_categories/{}'.format(  # noqa
            self.test_host,
            self.test_subcategory_translated.parent.slug,
            self.test_subcategory_translated.slug,
        )

        self.link_test_subcategory_translation = CategoryTranslation.objects.create(
            old_category=self.test_subcategory_translated,
            new_category=self.test_subcategory,
            text='For testing purposes we translate this category',
            created_by='someone@example.com',
        )

    @patch('signals.apps.api.v0.views.MlPredictCategoryView.ml_tool_client.predict')
    def test_predict(self, patched_ml_tool_client):
        response = mock.Mock()
        response.status_code = 200
        response.json = MagicMock(return_value={
            'hoofdrubriek': [[self.link_test_subcategory], [0.5]],
            'subrubriek': [[self.link_test_subcategory], [0.5]]
        })
        patched_ml_tool_client.return_value = response

        data = {'text': 'Give me the subcategory'}
        response = self.client.post(self.endpoint, data=data, format='json')

        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(response_json['subrubriek'][0][0], self.link_test_subcategory)

    @patch('signals.apps.api.v0.views.MlPredictCategoryView.ml_tool_client.predict')
    def test_predict_translated(self, patched_ml_tool_client):
        response = mock.Mock()
        response.status_code = 200
        response.json = MagicMock(return_value={
            'hoofdrubriek': [[self.link_test_subcategory_translated], [0.5]],
            'subrubriek': [[self.link_test_subcategory_translated], [0.5]]
        })
        patched_ml_tool_client.return_value = response

        data = {'text': 'Give me the subcategory, because of translations'}
        response = self.client.post(self.endpoint, data=data, format='json')

        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(response_json['subrubriek'][0][0], self.link_test_subcategory)

    @patch('signals.apps.api.v0.views.MlPredictCategoryView.ml_tool_client.predict',
           side_effect=ValidationError('error'))
    def test_predict_validation_error(self, patched_ml_tool_client):
        data = {'text': 'Give me the subcategory'}
        response = self.client.post(self.endpoint, data=data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()[0], 'error')
