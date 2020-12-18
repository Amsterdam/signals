import os

from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone

from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models import Attachment
from tests.apps.signals.attachment_helpers import (
    add_image_attachments,
    add_non_image_attachments,
    small_gif
)
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)
SIGNALS_TEST_DIR = os.path.join(os.path.split(THIS_DIR)[0], '..', '..', '..', 'signals')


@override_settings(FEATURE_FLAGS={
    'API_SEARCH_ENABLED': False,
    'SEARCH_BUILD_INDEX': False,
    'API_DETERMINE_STADSDEEL_ENABLED': False,
    'API_FILTER_EXTRA_PROPERTIES': False,
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER': False,
    'API_TRANSFORM_SOURCE_IF_A_SIGNAL_IS_A_CHILD': False,
    'API_VALIDATE_SOURCE_AGAINST_SOURCE_MODEL': False,
    'TASK_UPDATE_CHILDREN_BASED_ON_PARENT': False,
})
class TestPrivateSignalAttachmentsEndpoint(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    endpoint = '/signals/v1/private/signals/'
    test_host = 'http://testserver'

    def setUp(self):
        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))

    def test_image_upload(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal = SignalFactory.create()
        image = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')

        response = self.client.post(f'{self.endpoint}{signal.pk}/attachments/', data={'file': image})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(signal.attachments.count(), 1)
        self.assertIsInstance(signal.attachments.first(), Attachment)
        self.assertIsInstance(signal.attachments.filter(is_image=True).first(), Attachment)

    def test_attachment_upload(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal = SignalFactory.create()
        doc_upload = os.path.join(SIGNALS_TEST_DIR, 'sia-ontwerp-testfile.doc')
        with open(doc_upload, encoding='latin-1') as f:
            data = {"file": f}
            response = self.client.post(f'{self.endpoint}{signal.pk}/attachments/', data)

        self.assertEqual(response.status_code, 201)
        self.assertIsInstance(signal.attachments.first(), Attachment)
        self.assertIsNone(signal.attachments.filter(is_image=True).first())
        self.assertEqual(self.sia_read_write_user.email, signal.attachments.first().created_by)

    def test_create_has_attachments_false(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        initial_post_data = dict(
            text='Mensen in het cafe maken erg veel herrie',
            location=dict(
                geometrie=dict(
                    type='point',
                    coordinates=[4.90022563, 52.36768424]
                ),
                stadsdeel="A",
                buurt_code="A04i",
                address=dict(
                    openbare_ruimte="Amstel",
                    huisnummer=1,
                    huisletter="",
                    huisnummer_toevoeging="",
                    postcode="1011PN",
                    woonplaats="Amsterdam"
                ),
                extra_properties=dict(),
            ),
            category=dict(
                category_url='/signals/v1/public/terms/categories/overig/sub_categories/overig'
            ),
            reporter=dict(
                email='melder@example.com'
            ),
            incident_date_start=timezone.now().strftime('%Y-%m-%dT%H:%M'),
            source='Telefoon – ASC',
        )

        response = self.client.post(self.endpoint, initial_post_data, format='json')
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertFalse(data['has_attachments'])

    def test_has_attachments_true(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        signal = SignalFactory.create()

        non_image_attachments = add_non_image_attachments(signal, 1)
        image_attachments = add_image_attachments(signal, 2)
        non_image_attachments += add_non_image_attachments(signal, 1)

        total_attachments = len(non_image_attachments) + len(image_attachments)

        response = self.client.get(f'{self.endpoint}{signal.pk}', format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data['has_attachments'])

        response = self.client.get(data['_links']['sia:attachments']['href'], format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['count'], total_attachments)
        self.assertEqual(len(data['results']), total_attachments)

        self.assertFalse(data['results'][0]['is_image'])
        self.assertEqual(self.test_host + non_image_attachments[0].file.url, data['results'][0]['location'])

        self.assertTrue(data['results'][1]['is_image'])
        self.assertEqual(self.test_host + image_attachments[0].file.url, data['results'][1]['location'])

        self.assertTrue(data['results'][2]['is_image'])
        self.assertEqual(self.test_host + image_attachments[1].file.url, data['results'][2]['location'])

        self.assertFalse(data['results'][3]['is_image'])
        self.assertEqual(self.test_host + non_image_attachments[1].file.url, data['results'][3]['location'])
