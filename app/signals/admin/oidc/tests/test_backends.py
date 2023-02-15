# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Delta10 B.V.
from django.test import TestCase

from signals.admin.oidc.backends import AuthenticationBackend
from signals.apps.users.factories import UserFactory


class BackendsTest(TestCase):
    def test_filter_users_by_claims(self):
        user = UserFactory.create()

        claims = {
            'email': user.email
        }

        backend = AuthenticationBackend()
        users_from_backend = backend.filter_users_by_claims(claims)

        self.assertEqual(user, users_from_backend[0])

    def test_create_user(self):
        backend = AuthenticationBackend()
        result = backend.create_user({})

        self.assertEqual(result, None)

    def test_update_user(self):
        user = UserFactory.create()

        backend = AuthenticationBackend()
        result = backend.update_user(user, {})

        self.assertEqual(result, user)
