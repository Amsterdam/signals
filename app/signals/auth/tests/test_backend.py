# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Gemeente Amsterdam
from unittest.mock import Mock

import pytest
from django.contrib.auth.backends import BaseBackend
from django.test import TestCase
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from signals.apps.users.factories import SuperUserFactory
from signals.auth.backend import JWTAuthBackend


class TestJWTAuthBackend(TestCase):
    def setUp(self):
        self.backend = JWTAuthBackend(backend=Mock(BaseBackend))

    def test_authenticate_header(self) -> None:
        assert self.backend.authenticate_header(Mock(Request)) == 'Bearer realm="signals"'

    def test_authenticate_always_ok_user_not_found(self) -> None:
        with pytest.raises(AuthenticationFailed):
            self.backend.authenticate(Mock(Request))

    def test_authenticate_always_ok(self) -> None:
        super_user = SuperUserFactory.create(email='signals.admin@example.com')

        user, _ = self.backend.authenticate(Mock(Request))

        assert user == super_user

    def test_authenticate_inactive_user(self) -> None:
        SuperUserFactory.create(email='signals.admin@example.com', is_active=False)

        with pytest.raises(AuthenticationFailed):
            self.backend.authenticate(Mock(Request))
