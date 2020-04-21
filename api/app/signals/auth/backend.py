from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken

USER_NOT_AUTHORIZED = "User {} is not authorized"
USER_DOES_NOT_EXIST = -1


class JWTBearerTokenVerify(AccessToken):
    """
    Override __init__, to skip optional JTI claim verification
    """
    def __init__(self, token=None, verify=False):
        super(JWTBearerTokenVerify, self).__init__(token, verify)


class JWTAuthBackend(JWTAuthentication):
    """
    Override get user, use caching
    """
    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            exceptions.AuthenticationFailed("No token or required scope")

        # Now we know we have a Amsterdam municipal employee (may or may not be allowed acceess)
        # or external user with access to the `signals` application, we retrieve the Django user.
        user = cache.get(user_id)

        if user == USER_DOES_NOT_EXIST:
            raise exceptions.AuthenticationFailed(USER_NOT_AUTHORIZED.format(user_id))

        # We hit the database max once per 5 minutes, and then cache the results.
        if user is None:  # i.e. cache miss
            try:
                user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
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
    """
    def authenticate(self, request):
        # The Datapunt django_authorization middleware performs the OAuth2 authentication checks.
        auth_user, decoded_token = super(JWTAuthBackend, self).authenticate(request)

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
