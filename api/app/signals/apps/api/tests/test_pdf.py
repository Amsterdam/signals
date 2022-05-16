# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2022 Gemeente Amsterdam

from django.contrib.auth.models import Permission

from signals.apps.signals.factories import CategoryFactory, DepartmentFactory, SignalFactory
from signals.test.utils import SIAReadWriteUserMixin, SignalsBaseApiTestCase


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
            f'attachment;filename="{self.signal.get_id_display()}.pdf"'
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
