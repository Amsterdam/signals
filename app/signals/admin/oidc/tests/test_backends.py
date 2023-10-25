# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 - 2023 Delta10 B.V., Gemeente Amsterdam
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

    def test_filter_users_by_claims_empty_claim(self):
        for empty_value in [None, '', False, 0]:
            claims = {
                'email': empty_value
            }

            backend = AuthenticationBackend()
            users_from_backend = backend.filter_users_by_claims(claims)

            self.assertEqual(users_from_backend.count(), 0)
