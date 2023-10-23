# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.contrib.auth.models import AbstractUser, Permission
from pytest_bdd import given

from signals.apps.users.factories import GroupFactory, UserFactory


@given('there is a read write user', target_fixture='read_write_user')
def given_read_write_user() -> AbstractUser:
    user = UserFactory.create(
        first_name='SIA-READ-WRITE',
        last_name='User',
    )
    user.user_permissions.add(Permission.objects.get(codename='sia_read'))
    user.user_permissions.add(Permission.objects.get(codename='sia_write'))
    user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))

    permissions = Permission.objects.filter(codename__in=(
        'sia_signal_create_initial',
        'sia_signal_create_note',
        'sia_signal_change_status',
        'sia_signal_change_category',
        'sia_can_view_contact_details',
    ))
    sia_test_group = GroupFactory.create(name='Test Group')
    sia_test_group.permissions.add(*permissions)
    user.groups.add(sia_test_group)

    return user
