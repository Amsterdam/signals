# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from signals.apps.signals.factories import (
    CategoryFactory,
    DepartmentFactory,
    ImageAttachmentFactory,
    SignalFactory
)
from signals.apps.signals.models import Attachment
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestAttachmentPermissions(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    # Accessing Attachments must follow the same access rules as the signals.
    # Specifically: rules around categories and departments must be followed.
    detail_endpoint = '/signals/v1/private/signals/{}'
    attachments_endpoint = '/signals/v1/private/signals/{}/attachments/'
    attachments_endpoint_detail = '/signals/v1/private/signals/{}/attachments/{}'

    def setUp(self):
        self.department = DepartmentFactory.create()
        self.category = CategoryFactory.create(departments=[self.department])
        self.signal = SignalFactory.create(category_assignment__category=self.category)
        self.attachment = ImageAttachmentFactory.create(_signal=self.signal)

    def test_cannot_access_without_proper_department_detail(self):
        self.assertEqual(Attachment.objects.filter(_signal=self.signal).count(), 1)
        self.client.force_authenticate(user=self.sia_read_write_user)

        url = self.detail_endpoint.format(self.signal.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        url = self.attachments_endpoint.format(self.signal.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        url = self.attachments_endpoint_detail.format(self.signal.pk, self.attachment.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_can_access_with_proper_department(self):
        self.assertEqual(Attachment.objects.filter(_signal=self.signal).count(), 1)
        self.client.force_authenticate(user=self.sia_read_write_user)
        self.sia_read_write_user.profile.departments.add(self.department)

        url = self.detail_endpoint.format(self.signal.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        url = self.attachments_endpoint.format(self.signal.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        url = self.attachments_endpoint_detail.format(self.signal.pk, self.attachment.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
