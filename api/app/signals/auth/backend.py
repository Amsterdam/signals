from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework import exceptions

USER_NOT_AUTHORIZED = "User {} is not authorized"
USER_DOES_NOT_EXIST = -1


class JWTAuthBackend:
    """
    Authenticate. Check if required scope is present and get user_email from JWT token.
    """

    @staticmethod  # noqa: C901
    def authenticate(request):
        # The Datapunt django_authorization middleware performs the OAuth2 authentication checks.
        # Note: SIG/ALL is available to all Amsterdam municipal employees.
        scope = required_scope = 'SIG/ALL'
        if hasattr(request, "is_authorized_for") and request.is_authorized_for(required_scope):
            user_email = request.get_token_subject.lower()

            if user_email == "always_ok":
                user_email = settings.TEST_LOGIN
        else:
            raise exceptions.AuthenticationFailed("No token or required scope")

        # Now we know we have a Amsterdam municipal employee (may or may not be allowed acceess)
        # or external user with access to the `signals` application, we retrieve the Django user.
        user = cache.get(user_email)

        if user == USER_DOES_NOT_EXIST:
            raise exceptions.AuthenticationFailed(USER_NOT_AUTHORIZED.format(user_email))

        # We hit the database max once per 5 minutes, and then cache the results.
        if user is None:  # i.e. cache miss
            try:
                user = User.objects.get(username=user_email)
            except User.DoesNotExist:
                cache.set(user_email, USER_DOES_NOT_EXIST, 5 * 60)
                raise exceptions.AuthenticationFailed(USER_NOT_AUTHORIZED.format(user_email))
            else:
                cache.set(user_email, user, 5 * 60)

        # We return only when we have correct scope, and user is known to `signals`.
        return user, scope

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        return 'Bearer realm="signals"'
