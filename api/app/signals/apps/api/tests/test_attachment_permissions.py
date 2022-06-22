# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import os

from django.contrib.auth.models import Permission

from signals.apps.signals.factories import (
    CategoryFactory,
    DepartmentFactory,
    ImageAttachmentFactory,
    SignalFactory
)
from signals.apps.signals.models import Attachment, Note
from signals.test.utils import SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestAttachmentPermissions(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    detail_endpoint = '/signals/v1/private/signals/{}'
    attachments_endpoint = '/signals/v1/private/signals/{}/attachments/'
    attachments_endpoint_detail = '/signals/v1/private/signals/{}/attachments/{}'

    def setUp(self):
        self.department = DepartmentFactory.create()
        self.category = CategoryFactory.create(departments=[self.department])
        self.signal = SignalFactory.create(category_assignment__category=self.category)
        self.attachment = ImageAttachmentFactory.create(_signal=self.signal, created_by='ambtenaar@example.com')

        # Various Attachment delete permissions
        self.permission_delete_other = Permission.objects.get(codename='sia_delete_attachment_of_other_user')
        self.permission_delete_anonymous_user = Permission.objects.get(
            codename='sia_delete_attachment_of_anonymous_user')
        self.permission_delete_normal = Permission.objects.get(codename='sia_delete_attachment_of_normal_signal')
        self.permission_delete_parent = Permission.objects.get(codename='sia_delete_attachment_of_parent_signal')
        self.permission_delete_child = Permission.objects.get(codename='sia_delete_attachment_of_child_signal')

    # Rules for access to attachments:
    # Accessing Attachments must follow the same access rules as the signals.
    # Specifically: rules around categories and departments must be followed.
    # This test also checks that the special permissions around deletion of
    # attachments are followed.

    def test_cannot_access_without_proper_department_detail(self):  # WORKS
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

    def test_can_access_with_proper_department(self):  # WORKS
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

    # Rules for deletion of attachments:
    # 1: you need correct department to delete attachments
    # 2: you need correct permission to delete attachments. One or more of:
    #    - permission to delete a normal signal's attachments
    #    - permission to delete a parent signal's attachments
    #    - permission to delete a child signal's attachments
    # 3: you need extra permissions to delete attachments not uploaded
    #    by yourself. Your own attachments you can delete. Custom permissions:
    #    - permission to delete another Signalen user's attachment
    #    - permission to delete an anonymous user's (i.e. generally reporter's)
    #      attachment

    # Tests for point 1:
    def test_delete_without_proper_department(self):
        """
        Check that the rules around deletion are only checked after the normal
        access rules are checked (based on department).

        This test hands out all custom attachment deletion permissions but does
        not associate the test user with the correct department.
        """
        self.assertEqual(Attachment.objects.filter(_signal=self.signal).count(), 1)
        self.client.force_authenticate(user=self.sia_read_write_user)

        # hand out all of normal, parent, child signal's attachment delete permissions
        self.sia_read_write_user.user_permissions.set([
            self.permission_delete_other,
            self.permission_delete_anonymous_user,
            self.permission_delete_normal,
            self.permission_delete_parent,
            self.permission_delete_child,
        ])
        self.sia_read_write_user.save()
        self.sia_read_write_user.refresh_from_db()
        self.client.force_authenticate(user=self.sia_read_write_user)
        self.assertEqual(Note.objects.count(), 0)

        # cannot delete somebody else's attachments (to normal signal)
        url = self.attachments_endpoint_detail.format(self.signal.pk, self.attachment.pk)
        response = self.client.get(url)
        error_message = response.json()['detail']  # generic 403 message (translated hence not hardcoded below)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Note.objects.count(), 0)

        # cannot delete one's own attachments (to normal signal)
        self.attachment.created_by = self.sia_read_write_user.email
        self.attachment.save()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['detail'], error_message)
        self.assertEqual(Note.objects.count(), 0)

        # cannot delete parent signal's attachment (even uploaded by oneself)
        child_signal = SignalFactory.create(parent=self.signal, category_assignment__category=self.category)
        child_attachment = ImageAttachmentFactory.create(
            _signal=child_signal, created_by=self.sia_read_write_user.email)
        child_attachment_url = self.attachments_endpoint_detail.format(child_signal.pk, child_attachment.pk)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['detail'], error_message)
        self.assertEqual(Note.objects.count(), 0)

        # cannot delete child signal's attachment (even uploaded by oneself)
        response = self.client.get(child_attachment_url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['detail'], error_message)
        self.assertEqual(Note.objects.count(), 0)

        # nothing was deleted:
        self.assertEqual(Attachment.objects.filter(_signal=self.signal).count(), 1)
        self.assertEqual(Note.objects.filter(_signal=child_signal).count(), 0)

    # Tests for point 2:
    def test_delete_normal_signals_attachments(self):
        """
        Check that "sia_delete_attachment_of_normal_signal" is needed to delete a
        normal signal's attachments. Note: test uses the same user that uploaded
        to delete the attachments, so "sia_delete_attachment_of_anonymous_user" and
        "sia_delete_attachment_of_other_user" are not needed.
        """
        self.assertEqual(Attachment.objects.filter(_signal=self.signal).count(), 1)
        self.client.force_authenticate(user=self.sia_read_write_user)
        self.sia_read_write_user.profile.departments.add(self.department)

        # let's pretend our test user uploaded the attachment
        self.attachment.created_by = self.sia_read_write_user.email
        self.attachment.save()
        att_filename = os.path.basename(self.attachment.file.name)

        # Try to delete without "sia_delete_attachment_of_normal_signal"
        url = self.attachments_endpoint_detail.format(self.signal.pk, self.attachment.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Attachment.objects.filter(_signal=self.signal).count(), 1)

        # Try to delete with "sia_delete_attachment_of_normal_signal"
        self.sia_read_write_user.user_permissions.set([self.permission_delete_normal])
        self.sia_read_write_user.save()
        self.sia_read_write_user.refresh_from_db()
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Attachment.objects.filter(_signal=self.signal).count(), 0)
        self.assertEqual(Note.objects.filter(_signal=self.signal).count(), 1)

        n = Note.objects.all().first()
        self.assertEqual(n.text, f'Bijlage {att_filename} is verwijderd.')
        self.assertEqual(n.created_by, self.sia_read_write_user.email)

    def test_delete_parent_signal_attachments(self):
        """
        Check that "sia_delete_attachment_of_parent_signal" is needed to delete a
        parent signal's attachments. Note: test uses the same user that uploaded
        to delete the attachments, so "sia_delete_attachment_of_anonymous_user" and
        "sia_delete_attachment_of_other_user" are not needed.
        """
        self.assertEqual(Attachment.objects.filter(_signal=self.signal).count(), 1)
        self.client.force_authenticate(user=self.sia_read_write_user)
        self.sia_read_write_user.profile.departments.add(self.department)

        # Turn the signal into a parent signal, let's pretend our test
        # user uploaded its attachment.
        SignalFactory.create(parent=self.signal, category_assignment__category=self.category)
        self.attachment.created_by = self.sia_read_write_user.email
        self.attachment.save()
        att_filename = os.path.basename(self.attachment.file.name)

        # Try to delete without "sia_delete_attachment_of_parent_signal"
        parent_signal = self.signal
        parent_attachment = self.attachment
        parent_attachment_url = self.attachments_endpoint_detail.format(parent_signal.pk, parent_attachment.pk)

        response = self.client.delete(parent_attachment_url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Attachment.objects.filter(_signal=parent_signal).count(), 1)
        self.assertEqual(Note.objects.filter(_signal=parent_signal).count(), 0)
        self.assertIn('sia_delete_attachment_of_parent_signal', response.json()['detail'])

        # Try to delete with "delete_attachment_of_parent_signal"
        self.sia_read_write_user.user_permissions.set([self.permission_delete_parent])
        self.sia_read_write_user.save()
        self.sia_read_write_user.refresh_from_db()
        self.client.force_authenticate(user=self.sia_read_write_user)

        self.assertEqual(Note.objects.filter(_signal=parent_signal).count(), 0)
        response = self.client.delete(parent_attachment_url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Attachment.objects.filter(_signal=parent_signal).count(), 0)
        self.assertEqual(Note.objects.filter(_signal=parent_signal).count(), 1)

        n = Note.objects.all().first()
        self.assertEqual(n.text, f'Bijlage {att_filename} is verwijderd.')
        self.assertEqual(n.created_by, self.sia_read_write_user.email)

    def test_delete_child_signal_attachments(self):
        """
        Check that "sia_delete_attachment_of_child_signal" is needed to delete a
        child signal's attachments. Note: test uses the same user that uploaded
        to delete the attachments, so "sia_delete_attachment_of_anonymous_user" and
        "sia_delete_attachment_of_other_user" are not needed.
        """
        self.assertEqual(Attachment.objects.filter(_signal=self.signal).count(), 1)
        self.client.force_authenticate(user=self.sia_read_write_user)
        self.sia_read_write_user.profile.departments.add(self.department)

        # Create a child signal and attachment, let's pretend our test
        # user uploaded the attachment.
        child_signal = SignalFactory.create(parent=self.signal, category_assignment__category=self.category)
        child_attachment = ImageAttachmentFactory.create(
            _signal=child_signal, created_by=self.sia_read_write_user.email)
        att_filename = os.path.basename(child_attachment.file.name)

        # Try to delete without "sia_delete_attachment_of_child_signal"
        child_attachment_url = self.attachments_endpoint_detail.format(child_signal.pk, child_attachment.pk)

        response = self.client.delete(child_attachment_url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Attachment.objects.filter(_signal=child_signal).count(), 1)
        self.assertIn('sia_delete_attachment_of_child_signal', response.json()['detail'])

        # Try to delete with "sia_delete_attachment_of_child_signal"
        self.sia_read_write_user.user_permissions.set([self.permission_delete_child])
        self.sia_read_write_user.save()
        self.sia_read_write_user.refresh_from_db()
        self.client.force_authenticate(user=self.sia_read_write_user)

        self.assertEqual(Note.objects.filter(_signal=child_signal).count(), 0)
        response = self.client.delete(child_attachment_url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Attachment.objects.filter(_signal=child_signal).count(), 0)
        self.assertEqual(Note.objects.filter(_signal=child_signal).count(), 1)

        n = Note.objects.filter(_signal=child_signal).first()
        self.assertEqual(n.text, f'Bijlage {att_filename} is verwijderd.')
        self.assertEqual(n.created_by, self.sia_read_write_user.email)

    # Tests for point 3:
    def test_delete_own_attachments_no_extra_rights(self):
        """
        Test that user without "sia_delete_attachment_of_other_user" and without
        "sia_delete_attachment_of_anonymous_user" permission can delete their own
        attachments.
        """
        self.assertEqual(Attachment.objects.filter(_signal=self.signal).count(), 1)
        self.client.force_authenticate(user=self.sia_read_write_user)
        self.sia_read_write_user.profile.departments.add(self.department)
        att_filename = os.path.basename(self.attachment.file.name)

        # hand out all of normal, parent, child signal's attachment delete permissions
        self.sia_read_write_user.user_permissions.set([
            self.permission_delete_normal,
            self.permission_delete_parent,
            self.permission_delete_child,
        ])
        self.sia_read_write_user.save()
        self.sia_read_write_user.refresh_from_db()
        self.client.force_authenticate(user=self.sia_read_write_user)

        # let's pretend our test user uploaded the attachment
        self.attachment.created_by = self.sia_read_write_user.email
        self.attachment.save()

        # test user should be able to delete their own attachment
        self.assertEqual(Note.objects.filter(_signal=self.signal).count(), 0)
        url = self.attachments_endpoint_detail.format(self.signal.pk, self.attachment.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Attachment.objects.filter(_signal=self.signal).count(), 0)
        self.assertEqual(Note.objects.filter(_signal=self.signal).count(), 1)

        n = Note.objects.all().first()
        self.assertEqual(n.text, f'Bijlage {att_filename} is verwijderd.')
        self.assertEqual(n.created_by, self.sia_read_write_user.email)

    def test_delete_anonymous_users_attachments(self):
        """
        Test that user without "sia_delete_attachment_of_other_user" and without
        "sia_delete_attachment_of_anonymous_user" permission cannot delete an
        anonymous user's attachment.
        """
        self.assertEqual(Attachment.objects.filter(_signal=self.signal).count(), 1)
        self.client.force_authenticate(user=self.sia_read_write_user)
        self.sia_read_write_user.profile.departments.add(self.department)
        att_filename = os.path.basename(self.attachment.file.name)

        # let's pretend a anonymous user (i.e. never logged-in) uploaded the attachment
        self.attachment.created_by = None
        self.attachment.save()

        # hand out all of normal, parent, child signal's attachment delete permissions
        self.sia_read_write_user.user_permissions.set([
            self.permission_delete_normal,
            self.permission_delete_parent,
            self.permission_delete_child,
        ])
        self.sia_read_write_user.save()
        self.sia_read_write_user.refresh_from_db()
        self.client.force_authenticate(user=self.sia_read_write_user)
        attachment_url = self.attachments_endpoint_detail.format(self.signal.pk, self.attachment.pk)

        # Try to delete without "sia_delete_attachment_of_anonymous_user"
        self.assertEqual(Note.objects.filter(_signal=self.signal).count(), 0)
        response = self.client.delete(attachment_url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Attachment.objects.filter(_signal=self.signal).count(), 1)
        self.assertEqual(Note.objects.filter(_signal=self.signal).count(), 0)

        # Try to delete with "sia_delete_attachment_of_anonymous_user"
        self.sia_read_write_user.user_permissions.add(self.permission_delete_anonymous_user)
        self.sia_read_write_user.save()
        self.sia_read_write_user.refresh_from_db()
        self.client.force_authenticate(user=self.sia_read_write_user)

        self.assertEqual(Note.objects.filter(_signal=self.signal).count(), 0)
        response = self.client.delete(attachment_url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Attachment.objects.filter(_signal=self.signal).count(), 0)
        self.assertEqual(Note.objects.filter(_signal=self.signal).count(), 1)

        n = Note.objects.filter(_signal=self.signal).first()
        self.assertEqual(n.text, f'Bijlage {att_filename} is verwijderd.')
        self.assertEqual(n.created_by, self.sia_read_write_user.email)

    def test_delete_other_users_attachments_no_extra_rights(self):
        """
        Test that user without "sia_delete_attachment_of_other_user" and without
        "sia_delete_attachment_of_anonymous_user" permission cannot delete another
        user's attachments.
        """
        self.assertEqual(Attachment.objects.filter(_signal=self.signal).count(), 1)
        self.client.force_authenticate(user=self.sia_read_write_user)
        self.sia_read_write_user.profile.departments.add(self.department)
        att_filename = os.path.basename(self.attachment.file.name)

        # hand out all of normal, parent, child signal's attachment delete permissions
        self.sia_read_write_user.user_permissions.set([
            self.permission_delete_normal,
            self.permission_delete_parent,
            self.permission_delete_child,
        ])
        self.sia_read_write_user.save()
        self.sia_read_write_user.refresh_from_db()
        self.client.force_authenticate(user=self.sia_read_write_user)
        attachment_url = self.attachments_endpoint_detail.format(self.signal.pk, self.attachment.pk)

        # Try to delete without "sia_delete_attachment_of_other_user"
        self.assertEqual(Note.objects.filter(_signal=self.signal).count(), 0)
        response = self.client.delete(attachment_url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Attachment.objects.filter(_signal=self.signal).count(), 1)
        self.assertEqual(Note.objects.filter(_signal=self.signal).count(), 0)

        # Try to delete with "sia_delete_attachment_of_other_user"
        self.sia_read_write_user.user_permissions.add(self.permission_delete_other)
        self.sia_read_write_user.save()
        self.sia_read_write_user.refresh_from_db()
        self.client.force_authenticate(user=self.sia_read_write_user)

        self.assertEqual(Note.objects.filter(_signal=self.signal).count(), 0)
        response = self.client.delete(attachment_url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Attachment.objects.filter(_signal=self.signal).count(), 0)
        self.assertEqual(Note.objects.filter(_signal=self.signal).count(), 1)

        n = Note.objects.filter(_signal=self.signal).first()
        self.assertEqual(n.text, f'Bijlage {att_filename} is verwijderd.')
        self.assertEqual(n.created_by, self.sia_read_write_user.email)
