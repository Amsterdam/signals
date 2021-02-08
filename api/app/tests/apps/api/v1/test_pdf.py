from io import BytesIO
from unittest.mock import MagicMock

from django.contrib.auth.models import Permission
from django.test import override_settings
from PIL import Image

from signals.apps.api.v1.views import GeneratePdfView
from signals.apps.signals.factories import (
    AttachmentFactory,
    CategoryFactory,
    DepartmentFactory,
    SignalFactory
)
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestPDFView(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    def setUp(self):
        self.signal = SignalFactory.create()

    def test_get_pdf(self):
        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.client.force_authenticate(user=self.sia_read_write_user)
        url = '/signals/v1/private/signals/{}/pdf'.format(self.signal.pk)
        response = self.client.get(path=url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/pdf')
        self.assertEqual(
            response.get('Content-Disposition'),
            'attachment;filename="Signalen-{}.pdf"'.format(self.signal.pk)
        )

    def test_get_pdf_signal_does_not_exists(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        url = '/signals/v1/private/signals/{}/pdf'.format(999)
        response = self.client.get(path=url)

        self.assertEqual(response.status_code, 404)

    def test_get_pdf_signal_not_loggedin(self):
        self.client.logout()
        url = '/signals/v1/private/signals/{}/pdf'.format(999)
        response = self.client.get(path=url)

        self.assertEqual(response.status_code, 401)

    @override_settings(API_PDF_RESIZE_IMAGES_TO=800)
    def test_resize_image_too_wide(self):
        too_wide = MagicMock()
        too_wide.width = 1600
        too_wide.height = 800
        gpv = GeneratePdfView()
        gpv._resize(too_wide)

        too_wide.resize.assert_called_with(size=(800, 400), resample=Image.LANCZOS)

    @override_settings(API_PDF_RESIZE_IMAGES_TO=800)
    def test_resize_iamge_too_heigh(self):
        too_heigh = MagicMock()
        too_heigh.width = 800
        too_heigh.height = 1600
        gpv = GeneratePdfView()
        gpv._resize(too_heigh)

        too_heigh.resize.assert_called_with(size=(400, 800), resample=Image.LANCZOS)

    def test_get_context_data_no_images(self):
        AttachmentFactory(_signal=self.signal, file__filename='blah.txt', file__data=b'blah', is_image=False)
        gpv = GeneratePdfView()
        jpg_data_urls = gpv._get_context_data_images(self.signal)
        self.assertEqual(len(jpg_data_urls), 0)

    def test_get_context_data_invalid_images(self):
        AttachmentFactory.create(_signal=self.signal, file__filename='blah.jpg', file__data=b'blah', is_image=True)
        gpv = GeneratePdfView()
        jpg_data_urls = gpv._get_context_data_images(self.signal)
        self.assertEqual(len(jpg_data_urls), 0)

    @override_settings(API_PDF_RESIZE_IMAGES_TO=80)
    def test_get_context_data_valid_image(self):
        image = Image.new("RGB", (100, 100), (0, 0, 0))
        buffer = BytesIO()
        image.save(buffer, format='JPEG')

        AttachmentFactory.create(_signal=self.signal, file__filename='blah.jpg', file__data=buffer.getvalue())
        gpv = GeneratePdfView()
        jpg_data_urls = gpv._get_context_data_images(self.signal)
        self.assertEqual(len(jpg_data_urls), 1)
        self.assertEqual(jpg_data_urls[0][:22], 'data:image/jpg;base64,')
        self.assertGreater(len(jpg_data_urls[0]), 22)


class TestPDFPermissions(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    # Accessing PDFs must follow the same access rules as the signals.
    # Specifically: rules around categories and departments must be followed.
    detail_endpoint = '/signals/v1/private/signals/{}'
    pdf_endpoint = '/signals/v1/private/signals/{}/pdf'

    def setUp(self):
        self.department = DepartmentFactory.create()
        self.category = CategoryFactory.create(departments=[self.department])
        self.signal = SignalFactory.create(category_assignment__category=self.category)

    def test_assumptions(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        url = self.detail_endpoint.format(self.signal.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_cannot_access_without_proper_department(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        url = self.pdf_endpoint.format(self.signal.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_can_access_with_proper_department(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        self.sia_read_write_user.profile.departments.add(self.department)
        url = self.pdf_endpoint.format(self.signal.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
