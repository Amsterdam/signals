from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework import exceptions

from .tokens import JWTAccessToken

USER_NOT_AUTHORIZED = "User {} is not authorized"
USER_DOES_NOT_EXIST = -1


class JWTAuthBackend():
    """
    Retrieve user from backend and cache the result
    """
    @staticmethod  # noqa: C901
    def get_user(user_id):
        # Now we know we have a Amsterdam municipal employee (may or may not be allowed acceess)
        # or external user with access to the `signals` application, we retrieve the Django user.
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
        authz_header = request.META.get('HTTP_AUTHORIZATION')
        claims, user_id = JWTAccessToken.token_data(authz_header)
        if user_id == "ALWAYS_OK":
            user_id = settings.TEST_LOGIN

        auth_user = JWTAuthBackend.get_user(user_id)
        # We return only when we have correct scope, and user is known to `signals`.
        # TODO remove default empty scope
        return auth_user, ''

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        return 'Bearer realm="signals"'
