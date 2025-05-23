# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2023 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
import datetime
import os
from unittest import mock

import pytest
import pytz
from django.contrib.auth.models import Permission, User
from django.contrib.gis.geos import Point
from django.test import TestCase, override_settings
from django.utils import timezone
from freezegun import freeze_time
from PIL import Image

from signals.apps.history.services import SignalLogService
from signals.apps.services.domain.pdf import IsPdfChecker, PDFSummaryService
from signals.apps.signals import workflow
from signals.apps.signals.factories import (
    CategoryFactory,
    LocationFactory,
    ParentCategoryFactory,
    SignalFactoryWithImage,
    StatusFactory,
    ValidLocationFactory
)
from signals.apps.users.factories import SuperUserFactory, UserFactory


class TestPDFSummaryService(TestCase):
    """
    These tests check the contents of PDFs generated byt the PDFSummaryService.
    We do not want to parse PDFs, instead we look at the content of the intermediate
    HTML.
    """
    def setUp(self):
        self.parent_category = ParentCategoryFactory.create(name='PARENT-CATEGORY')
        self.child_category = CategoryFactory.create(name='CHILD-CATEGORY', parent=self.parent_category)

        self.signal = SignalFactoryWithImage.create(
            text='BLAH BLAH BLAH',
            incident_date_start=timezone.now(),
            category_assignment__category=self.child_category,
            reporter__email='foo@bar.com',
            reporter__phone='0612345678',
            location__geometrie=Point(4.9000607, 52.3675707))  # location of city hall / Stopera
        SignalLogService.log_create_initial(self.signal)

        status = StatusFactory.create(_signal=self.signal, state=workflow.AFWACHTING, text='waiting')
        SignalLogService.log_update_status(status)

        status = StatusFactory.create(_signal=self.signal, state=workflow.ON_HOLD, text='please hold')
        SignalLogService.log_update_status(status)

        status = StatusFactory.create(_signal=self.signal, state=workflow.AFGEHANDELD, text='Consider it done')
        SignalLogService.log_update_status(status)

        self.signal.status = status
        self.signal.save()

        self.user = SuperUserFactory.create()

    def test_get_html(self):
        html = PDFSummaryService._get_html(self.signal, self.user, False)

        # General information about the `Signal` object.
        current_tz = timezone.get_current_timezone()
        self.assertIn(self.signal.get_id_display(), html)
        self.assertIn(self.signal.created_at.astimezone(current_tz).strftime('%d-%m-%Y'), html)
        self.assertIn(self.signal.created_at.astimezone(current_tz).strftime('%H:%M'), html)
        self.assertIn(self.signal.incident_date_start.astimezone(current_tz).strftime('%d-%m-%Y'), html)
        self.assertIn(self.signal.incident_date_start.astimezone(current_tz).strftime('%H:%M'), html)
        self.assertIn(self.signal.get_id_display(), html)
        self.assertIn(self.signal.category_assignment.category.parent.name, html)
        self.assertIn(self.signal.category_assignment.category.name, html)
        self.assertIn(self.signal.priority.get_priority_display(), html)
        self.assertIn(self.signal.text, html)
        self.assertIn(self.signal.location.get_stadsdeel_display(), html)
        self.assertIn(self.signal.location.address_text, html)
        self.assertIn(self.signal.source, html)

        # All status transitions.
        for status in self.signal.statuses.all():
            self.assertIn(status.state, html)
            self.assertIn(status.text, html)
            self.assertIn(status.user, html)

    @mock.patch('signals.apps.services.domain.pdf.PDFSummaryService._get_context_data', autospec=True)
    def test_get_pdf(self, patched):
        patched.return_value = {}
        pdf = PDFSummaryService.get_pdf(self.signal, self.user, False)
        self.assertGreater(len(pdf), 0)

    def test_get_contact_details(self):
        """
        Users without "signals.sia_can_view_contact_details" permission cannot
        see contact details of the reporter. PDFs generated for use with
        CityControl always contain the contact details.

        This test checks the PDFSummaryService._get_contact_details method.
        """
        # No "signals.sia_can_view_contact_details" and no CityControl/Sigmax
        # override mean no contact details.
        user = UserFactory.create()
        email, phone = PDFSummaryService._get_contact_details(self.signal, user, False)
        self.assertFalse(user.has_perm('signals.sia_can_view_contact_details'))
        self.assertEqual(email, '*****')
        self.assertEqual(phone, '*****')

        # Check CityControl/Sigmax override
        email, phone = PDFSummaryService._get_contact_details(self.signal, None, True)
        self.assertEqual(email, 'foo@bar.com')
        self.assertEqual(phone, '0612345678')

        # Check user has "signals.sia_can_view_contact_details"
        sia_can_view_contact_details = Permission.objects.get(codename='sia_can_view_contact_details')
        user.user_permissions.add(sia_can_view_contact_details)
        user = User.objects.get(pk=user.id)

        self.assertTrue(user.has_perm('signals.sia_can_view_contact_details'))
        email, phone = PDFSummaryService._get_contact_details(self.signal, user, False)
        self.assertEqual(email, 'foo@bar.com')
        self.assertEqual(phone, '0612345678')

    def test_get_contact_details_no_contact_details_and_no_permissions(self):
        """
        Check that missing contact details are not turned into '*****' when not
        allowed to view reporter contact details.
        """
        self.signal.reporter.email = None
        self.signal.reporter.phone = None
        self.signal.reporter.save()
        self.signal.refresh_from_db()

        user = UserFactory.create()
        self.assertFalse(user.has_perm('signals.sia_can_view_contact_details'))
        email, phone = PDFSummaryService._get_contact_details(self.signal, user, False)
        self.assertEqual(email, None)
        self.assertEqual(phone, None)

    def test_show_contact_details(self):
        """
        Users without "signals.sia_can_view_contact_details" permission cannot
        see contact details of the reporter. PDFs generated for use with
        CityControl always contain the contact details.

        This test checks the intermediate HTML does or does not contain the
        contact details as appropriate.
        """
        # No "signals.sia_can_view_contact_details" and no CityControl/Sigmax
        # override mean no contact details in intermediate HTML.
        user = UserFactory.create()
        html = PDFSummaryService._get_html(self.signal, user, False)
        self.assertFalse(user.has_perm('signals.sia_can_view_contact_details'))
        self.assertNotIn('foo@bar.com', html)
        self.assertNotIn('0612345678', html)

        # Check CityControl/Sigmax override
        html = PDFSummaryService._get_html(self.signal, None, True)
        self.assertIn('foo@bar.com', html)
        self.assertIn('0612345678', html)

        # Check user has "signals.sia_can_view_contact_details"
        sia_can_view_contact_details = Permission.objects.get(codename='sia_can_view_contact_details')
        user.user_permissions.add(sia_can_view_contact_details)
        user = User.objects.get(pk=user.id)

        self.assertTrue(user.has_perm('signals.sia_can_view_contact_details'))
        html = PDFSummaryService._get_html(self.signal, user, False)
        self.assertIn('foo@bar.com', html)
        self.assertIn('0612345678', html)

    def test_location_has_stadsdeel(self):
        # test stadsdeel present
        location = ValidLocationFactory.create(_signal=self.signal)
        self.signal.location = location
        self.signal.save()
        self.signal.refresh_from_db()

        html = PDFSummaryService._get_html(self.signal, None, False)
        self.assertIn(self.signal.location.get_stadsdeel_display(), html)

    def test_location_has_area_code_and_area_name(self):
        # test area_name and area_code present
        location = LocationFactory.create(
            _signal=self.signal, area_name='AREA-NAME', area_code='AREA-CODE', stadsdeel=None)
        self.signal.location = location
        self.signal.save()
        self.signal.refresh_from_db()

        html = PDFSummaryService._get_html(self.signal, None, False)
        self.assertIn(self.signal.location.area_name, html)
        self.assertNotIn(self.signal.location.area_code, html)

    def test_location_has_no_area_name_and_area_code(self):
        # test only area_code present
        location = LocationFactory.create(_signal=self.signal, area_name=None, area_code='AREA-CODE', stadsdeel=None)
        self.signal.location = location
        self.signal.save()
        self.signal.refresh_from_db()

        html = PDFSummaryService._get_html(self.signal, None, False)
        self.assertIn(self.signal.location.area_code, html)

    @override_settings(DEFAULT_MAP_TILE_SERVER='')
    def test_get_map_data_wms(self):
        bbox, img_data_uri = PDFSummaryService._get_map_data(self.signal)
        self.assertEqual(img_data_uri, None)

        # About the magic numbers below:
        # We use the Amsterdam City Hall in this test, coordinates were looked
        # up in WGS84 and RD coordinates (using data.amsterdam.nl).
        # WGS84 (lon, lat) = (4.9000607, 52.3675707) <=>
        # RD (x, y) = (121821.68, 486743.44)
        xmin, ymin, xmax, ymax = (float(value) for value in bbox.split(','))
        # We demand coordinates match to within a tenth of a meter, well below
        # the pixel size in the retrieved map.
        self.assertEqual(round(xmin - (121821.68 - 340), 1), 0)
        self.assertEqual(round(ymin - (486743.44 - 125), 1), 0)
        self.assertEqual(round(xmax - (121821.68 + 340), 1), 0)
        self.assertEqual(round(ymax - (486743.44 + 125), 1), 0)

    @override_settings(DEFAULT_MAP_TILE_SERVER='TESTSERVER')
    @mock.patch('signals.apps.services.domain.pdf.WMTSMapGenerator.make_map')
    def test_get_map_data_wmts(self, patched):
        map_img = Image.new("RGBA", (100, 100), 0)
        patched.return_value = map_img

        bbox, img_data_uri = PDFSummaryService._get_map_data(self.signal)
        self.assertEqual(bbox, None)
        self.assertTrue(img_data_uri.startswith('data:image/png;base64,'))
        self.assertGreater(len(img_data_uri), len('data:image/png;base64,'))

        patched.assert_called_once_with(
            url_template='TESTSERVER',
            lat=self.signal.location.geometrie.coords[1],
            lon=self.signal.location.geometrie.coords[0],
            zoom=17,
            img_size=[680, 250]
        )

    def test_get_logo_data_no_url(self):
        self.assertEqual(PDFSummaryService._get_logo_data(''), '')
        self.assertEqual(PDFSummaryService._get_logo_data(None), '')

    def test_get_logo_data_wrong_format(self):
        self.assertEqual(PDFSummaryService._get_logo_data('/dit/is/een.html'), '')
        self.assertEqual(PDFSummaryService._get_logo_data('https://example.com/dit/is/een.html'), '')

    def test_get_logo_data_wrong_scheme(self):
        self.assertEqual(PDFSummaryService._get_logo_data('ftp://example.com/dit/is/een.png'), '')

    @mock.patch(
        'signals.apps.services.domain.pdf.PDFSummaryService._get_logo_data_from_static_file', autospec=True)
    def test_get_logo_data_calls_get_logo_data_from_static_file(self, patched):
        PDFSummaryService._get_logo_data('/dit/is/een.png')
        patched.assert_called_once_with('/dit/is/een.png')

    @mock.patch(
        'signals.apps.services.domain.pdf.PDFSummaryService._get_logo_data_from_remote_url', autospec=True)
    def test_get_logo_data_calls_get_logo_data_from_remote_url(self, patched):
        PDFSummaryService._get_logo_data('https://example.com/dit/is/een.png')
        patched.assert_called_once_with('https://example.com/dit/is/een.png')

    @mock.patch(
         'signals.apps.services.domain.pdf.PDFSummaryService._get_logo_data_from_static_file', autospec=True)
    def test_get_logo_data_using_a_static_url(self, patched):
        patched.return_value = 'PNG'
        self.assertEqual(PDFSummaryService._get_logo_data('/dit/is/een.png'), 'data:image/png;base64,PNG')

    @mock.patch(
         'signals.apps.services.domain.pdf.PDFSummaryService._get_logo_data_from_remote_url', autospec=True)
    def test_get_logo_data_using_a_remote_url(self, patched):
        patched.return_value = 'PNG'
        self.assertEqual(
            PDFSummaryService._get_logo_data('https://example.com/dit/is/een.png'), 'data:image/png;base64,PNG')

    def test_logo_data_from_static_file_file_exists(self):
        # Use a known static file, the Amsterdan logo, for this test.
        svg = PDFSummaryService._get_logo_data_from_static_file('api/logo-gemeente-amsterdam.svg')
        self.assertEqual(type(svg), str)
        self.assertGreater(len(svg), 0)

    def test_logo_data_from_static_file_suspicious_file(self):
        # Static files can only use relative paths
        data = PDFSummaryService._get_logo_data_from_static_file('/root/in/path/not/allowed.png')
        self.assertEqual(data, '')

    def test_logo_data_from_static_file_file_does_not_exist(self):
        data = PDFSummaryService._get_logo_data_from_static_file('this/file/does/not/exist/anywhere')
        self.assertEqual(data, '')

    @override_settings(TIME_ZONE='UTC')
    def test_pdf_has_history_i(self):
        test_time = datetime.datetime(2022, 1, 1, 12, 0, 0, 0, tzinfo=pytz.UTC)
        with freeze_time(test_time):
            new_status = StatusFactory.create(
                _signal=self.signal, state=workflow.AFWACHTING, text='SHOULD BE IN HISTORY')
            self.signal.status = new_status
            self.signal.save()
            SignalLogService.log_update_status(new_status)

        self.signal.refresh_from_db()
        date_string = test_time.strftime('%d-%m-%Y')
        time_string = test_time.strftime('%H:%M:%S')

        html = PDFSummaryService._get_html(self.signal, None, False)
        self.assertIn('SHOULD BE IN HISTORY', html)
        self.assertIn(date_string, html)
        self.assertIn(time_string, html)

        html = PDFSummaryService._get_html(self.signal, None, True)
        self.assertIn('SHOULD BE IN HISTORY', html)
        self.assertIn(date_string, html)
        self.assertIn(time_string, html)

        html = PDFSummaryService._get_html(self.signal, self.user, False)
        self.assertIn('SHOULD BE IN HISTORY', html)
        self.assertIn(date_string, html)
        self.assertIn(time_string, html)

        html = PDFSummaryService._get_html(self.signal, self.user, True)
        self.assertIn('SHOULD BE IN HISTORY', html)
        self.assertIn(date_string, html)
        self.assertIn(time_string, html)


class TestPDFSummaryServiceWithExtraProperties(TestCase):
    def setUp(self):
        # Note: this test assumes Amsterdam categories being present, hence it being isolated.
        self.extra_properties_data = [
            {
                "id": "extra_straatverlichting",
                "label": "Is de situatie gevaarlijk?",
                "answer": {
                    "id": "niet_gevaarlijk",
                    "label": "Niet gevaarlijk"
                },
                "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/lantaarnpaal-straatverlichting"  # noqa
            },
        ]

        self.signal = SignalFactoryWithImage.create(
            extra_properties=self.extra_properties_data,
            category_assignment__category__parent__name='Wegen, verkeer, straatmeubilair',
            category_assignment__category__name='lantaarnpaal straatverlichting'
        )

    def test_extra_properties(self):
        html = PDFSummaryService._get_html(self.signal, None, False)

        self.assertIn('Is de situatie gevaarlijk?', html)
        self.assertIn('Niet gevaarlijk', html)


class TestIsPdfChecker:
    @pytest.mark.parametrize('path,expected', [
        (os.path.join(os.path.dirname(__file__), '../test-data/test.jpg'), False),
        (os.path.join(os.path.dirname(__file__), '../test-data/test.gif'), False),
        (os.path.join(os.path.dirname(__file__), '../test-data/test.png'), False),
        (os.path.join(os.path.dirname(__file__), '../test-data/test.svg'), False),
        (os.path.join(os.path.dirname(__file__), '../test-data/empty.txt'), False),
        (os.path.join(os.path.dirname(__file__), '../test-data/sia-ontwerp-testfile.doc'), False),
        (os.path.join(os.path.dirname(__file__), '../test-data/sia-ontwerp-testfile.pdf'), True),
    ])
    def test_checking(self, path, expected):
        is_pdf = IsPdfChecker(path)
        assert expected == is_pdf()

    def test_checking_file_that_does_not_exist(self):
        is_pdf = IsPdfChecker('/tmp/non-existing-file.1234')
        with pytest.raises(FileNotFoundError):
            is_pdf()

    def test_checking_with_file_instead_of_path(self):
        is_pdf = IsPdfChecker(open(
            os.path.join(os.path.dirname(__file__), '../test-data/sia-ontwerp-testfile.pdf'),
            'rb'
        ))
        assert is_pdf() is True
