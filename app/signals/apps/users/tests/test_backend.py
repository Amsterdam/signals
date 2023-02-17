# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
from unittest import mock, skip

from django.conf import settings
from django.test import TestCase
from rest_framework import exceptions

from signals.apps.users.factories import SuperUserFactory, UserFactory
from signals.auth import backend
from signals.auth.config import get_settings


class TestJWTAuthBackend(TestCase):
    def setUp(self):
        self.super_user = SuperUserFactory.create(email='superuser@example.com')
        self.normal_user = UserFactory.create(
            username='normie@example.com',
            email='normie@example.com',
        )

    @skip("Scope test are not required")
    def test_missing_scope(self):
        jwt_auth_backend = backend.JWTAuthBackend()

        mocked_request = mock.Mock()
        mocked_request.is_authorized_for.return_value = False

        with self.assertRaises(exceptions.AuthenticationFailed):
            jwt_auth_backend.authenticate(mocked_request)

    @mock.patch('signals.auth.tokens.JWTAccessToken.token_data')
    @mock.patch('signals.auth.backend.cache')
    def test_with_scope_wrong_user_cache_miss(self, mocked_cache, mock_token_data):
        jwt_auth_backend = backend.JWTAuthBackend()

        mocked_request = mock.Mock()
        mocked_request.is_authorized_for.return_value = True
        settings = get_settings()

        for user_id_fields in settings['USER_ID_FIELDS']:
            claims = {user_id_fields: 'wrong_user@example.com'}
            mock_token_data.return_value = claims, 'wrong_user@example.com'
            mocked_cache.get.return_value = None

            with self.assertRaises(exceptions.AuthenticationFailed):
                jwt_auth_backend.authenticate(mocked_request)

            mocked_cache.get.assert_called_once_with('wrong_user@example.com')
            mocked_cache.set.assert_called_once_with(
                'wrong_user@example.com',
                backend.USER_DOES_NOT_EXIST,
                5 * 60
            )
            mocked_cache.reset_mock()

    @mock.patch('signals.auth.tokens.JWTAccessToken.token_data')
    @mock.patch('signals.auth.backend.cache')
    @mock.patch('signals.auth.backend.User')
    def test_with_scope_wrong_user_cache_hit(self, mocked_user_model, mocked_cache, mock_token_data):
        jwt_auth_backend = backend.JWTAuthBackend()

        mocked_request = mock.Mock()
        mocked_request.is_authorized_for.return_value = True
        settings = get_settings()
        for user_id_field in settings['USER_ID_FIELDS']:
            claims = {user_id_field: 'wrong_user@example.com'}
            mock_token_data.return_value = claims, 'wrong_user@example.com'

            mocked_cache.get.return_value = backend.USER_DOES_NOT_EXIST

            with self.assertRaises(exceptions.AuthenticationFailed):
                jwt_auth_backend.authenticate(mocked_request)
            mocked_cache.get.assert_called_once_with('wrong_user@example.com')
            mocked_user_model.objects.get.assert_not_called()
            mocked_cache.reset_mock()

    @mock.patch('signals.auth.tokens.JWTAccessToken.token_data')
    @mock.patch('django.core.cache.cache')
    def test_with_scope_correct_user(self, mocked_cache, mock_token_data):
        jwt_auth_backend = backend.JWTAuthBackend()

        mocked_request = mock.Mock()
        mocked_request.is_authorized_for.return_value = True
        settings = get_settings()

        for user_id_field in settings['USER_ID_FIELDS']:
            claims = {user_id_field: 'normie@example.com'}
            mock_token_data.return_value = claims, 'normie@example.com'

            user, scope = jwt_auth_backend.authenticate(mocked_request)
            self.assertEqual(user, self.normal_user)
            # self.assertEqual(scope, 'SIG/ALL')

    @skip('TODO fix test')
    @mock.patch('signals.auth.backend.cache')
    def test_get_token_subject_is_none(self, mocked_cache):
        # In case the subject is not set on the JWT token (as the `sub claim`).
        # This test demonstrates the problem. See SIG-889 for next steps.

        jwt_auth_backend = backend.JWTAuthBackend()

        mocked_request = mock.Mock()
        mocked_request.is_authorized_for.return_value = True
        mocked_request.get_token_subject = None

        mocked_cache.get.return_value = None  # Force database lookup

        with self.assertRaises(AttributeError):
            jwt_auth_backend.authenticate(mocked_request)

    # --- Note ---
    # For local development the "always_ok" user with email=settings.TEST_LOGIN
    # must be present to bypass the OAuth2 check. Previous versions of the
    # JWTAuthBackend created a superuser with email=settings.ADMIN_LOGIN. These
    # two settings were equal allowing the always_ok user to authenticate and
    # pass all permissions checks.
    #
    # For local development the email=settings.TEST_LOGIN user should have
    # superuser priviliges (otherwise you will not be able to view all the
    # API pages generated by DRF).
    #
    # The following two tests check the behavior connected to the email=TEST_LOGIN
    # user.
    # ---

    @mock.patch('signals.auth.backend.cache')
    def test_no_test_login_user(self, mocked_cache):

        jwt_auth_backend = backend.JWTAuthBackend()

        mocked_request = mock.Mock()
        mocked_request.is_authorized_for.return_value = True
        mocked_request.get_token_subject = 'always_ok'

        mocked_cache.get.return_value = None  # Force database lookup

        with self.assertRaises(exceptions.AuthenticationFailed):
            jwt_auth_backend.authenticate(mocked_request)

    @mock.patch('signals.auth.backend.cache')
    def test_with_test_login_user(self, mocked_cache):
        test_user = SuperUserFactory.create(
            username=settings.TEST_LOGIN,
            email=settings.TEST_LOGIN,
        )
        jwt_auth_backend = backend.JWTAuthBackend()

        mocked_request = mock.Mock()
        mocked_request.is_authorized_for.return_value = True
        mocked_request.get_token_subject = 'always_ok'

        mocked_cache.get.return_value = None  # Force database lookup

        user, scope = jwt_auth_backend.authenticate(mocked_request)
        self.assertEqual(user, test_user)
        # self.assertEqual(scope, 'SIG/ALL')
