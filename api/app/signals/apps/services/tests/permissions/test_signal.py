# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings

from signals.apps.services.domain.permissions.signal import PermissionService
from signals.apps.signals.factories import SignalFactory


class TestSignalPermissionService(TestCase):
    def setUp(self):
        user_model = get_user_model()

        self.superuser, _ = user_model.objects.get_or_create(
            username='signals.admin@example.com', email='signals.admin@example.com', is_superuser=True,
            defaults={'first_name': 'John', 'last_name': 'Doe', 'is_staff': True}
        )

        self.user, _ = user_model.objects.get_or_create(
            username='signals.jane.doe@example.com', email='signals.jane.doe@example.com', is_superuser=False,
            defaults={'first_name': 'Jane', 'last_name': 'Doe', 'is_staff': False}
        )

        self.signal = SignalFactory.create()

    def test_super_user_has_permission(self):
        self.assertTrue(PermissionService.has_permission(self.superuser, 'signals.sia_read'))
        self.assertTrue(PermissionService.has_permission(self.superuser, 'signals.sia_read', self.signal))

        self.assertFalse(PermissionService.has_permission(self.user, 'signals.sia_read'))
        self.assertFalse(PermissionService.has_permission(self.user, 'signals.sia_read', self.signal))

    def test_super_user_has_permissions(self):
        self.assertTrue(PermissionService.has_permissions(self.superuser, ['signals.sia_read', 'signals.sia_write']))
        self.assertTrue(PermissionService.has_permissions(self.superuser, ['signals.sia_read', 'signals.sia_write'],
                                                          self.signal))

        self.assertFalse(PermissionService.has_permissions(self.user, ['signals.sia_read', 'signals.sia_write']))
        self.assertFalse(PermissionService.has_permissions(self.user, ['signals.sia_read', 'signals.sia_write'],
                                                           self.signal))

    def test_super_user_has_permission_via_routing(self):
        self.assertTrue(PermissionService.has_permission_via_department_routing(self.superuser, self.signal))

        self.assertFalse(PermissionService.has_permission_via_department_routing(self.user, self.signal))

    def test_super_user_has_permission_via_category(self):
        self.assertTrue(PermissionService.has_permission_via_category(self.superuser, self.signal))

        self.assertFalse(PermissionService.has_permission_via_category(self.user, self.signal))

    def test_super_user_has_signal_permission(self):
        self.assertTrue(PermissionService.has_signal_permission(self.superuser, self.signal))

        self.assertFalse(PermissionService.has_signal_permission(self.user, self.signal))

    @override_settings(FEATURE_FLAGS={'SKIP_PERMISSION_VIA_CATEGORY': True})
    def test_permission_via_category_check_disabled(self):
        self.assertTrue(PermissionService.has_permission_via_category(self.user, self.signal))

    @override_settings(FEATURE_FLAGS={'SKIP_PERMISSION_VIA_DEPARTMENT_ROUTING': True})
    def test_permission_via_department_routing_check_disabled(self):
        self.assertTrue(PermissionService.has_permission_via_department_routing(self.user, self.signal))

    @override_settings(FEATURE_FLAGS={'SKIP_PERMISSION_VIA_CATEGORY': True,
                                      'SKIP_PERMISSION_VIA_DEPARTMENT_ROUTING': True})
    def test_super_user_has_signal_permission_permission_checks_disabled(self):
        sia_read = Permission.objects.get(codename='sia_read')
        self.user.user_permissions.add(sia_read)

        self.assertTrue(PermissionService.has_signal_permission(self.user, self.signal))
