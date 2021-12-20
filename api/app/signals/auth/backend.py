# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from rest_framework import exceptions

from .tokens import JWTAccessToken

USER_NOT_AUTHORIZED = 'User {} is not authorized'
USER_DOES_NOT_EXIST = -1


class JWTAuthBackend:
    """
    Retrieve user from backend and cache the result
    """
    @staticmethod  # noqa: C901
    def get_user(user_id):
        # Now we know we have an Amsterdam municipal employee (may or may not be allowed access)
        # or external user with access to the `signals` application, we retrieve the Django user.
        user_id = user_id if user_id != 'ALWAYS_OK' else settings.TEST_LOGIN
        user = cache.get(user_id)

        if user == USER_DOES_NOT_EXIST:
            raise exceptions.AuthenticationFailed(USER_NOT_AUTHORIZED.format(user_id))

        # We hit the database max once per 5 minutes, and then cache the results.
        if user is None:  # i.e. cache miss
            try:
                user = User.objects.get(username__iexact=user_id)  # insensitive match fixes log-in bug
            except User.DoesNotExist:
                cache.set(user_id, USER_DOES_NOT_EXIST, 5 * 60)
                raise exceptions.AuthenticationFailed(USER_NOT_AUTHORIZED.format(user_id))
            else:
                cache.set(user_id, user, 5 * 60)

        if not user.is_active:
            raise exceptions.AuthenticationFailed('User inactive')
        return user

    """
    Authenticate. Check if required scope is present and get user_email from JWT token.
    use ALWAYS_OK = True to skip token verification. Useful for local dev/testing
    """
    @staticmethod  # noqa: C901
    def authenticate(request):
        claims, user_id = JWTAccessToken.token_data(request.META.get('HTTP_AUTHORIZATION'))
        auth_user = JWTAuthBackend.get_user(user_id)
        JWTAuthBackend.store_last_authentication(auth_user, claims)
        return auth_user, ''  # TODO Get rid of the empty scope

    @staticmethod
    def store_last_authentication(auth_user, claims):
        """
        In the keycloak token the "auth_time" claim is present. If it is present check if this is a later date then the
        previously stored "auth_time". If so update the user profile last_authentication.

        "auth_time" as explained on https://openid.net/specs/openid-connect-core-1_0.html#IDToken

            Time when the End-User authentication occurred. Its value is a JSON number representing the number of
            seconds from 1970-01-01T0:0:0Z as measured in UTC until the date/time. When a max_age request is made or
            when auth_time is requested as an Essential Claim, then this Claim is REQUIRED; otherwise, its inclusion is
            OPTIONAL. (The auth_time Claim semantically corresponds to the OpenID 2.0 PAPE [OpenID.PAPE] auth_time
            response parameter.)
        """
        if not settings.FEATURE_FLAGS.get('STORE_CLAIM_AUTH_TIME', False):
            # Feature disabled so just return None
            return None

        # Check if the "auth_time" claim is present
        if 'auth_time' in claims and claims['auth_time']:
            auth_time_claim = timezone.datetime.fromtimestamp(claims['auth_time'])

            # Check if the "auth_time" in the claims is later than the "last_authentication"
            if (auth_user.profile.last_authentication is None
                    or auth_user.profile.last_authentication.timestamp() < auth_time_claim.timestamp()):
                # Store the "auth_time" as "last_authentication"
                auth_user.profile.last_authentication = auth_time_claim
                auth_user.profile.save(update_fields=['last_authentication', 'updated_at'])

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        return 'Bearer realm="signals"'
