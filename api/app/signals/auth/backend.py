from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.core.cache import cache
from rest_framework import exceptions


class JWTAuthBackend:
    """
    Authenticate. Check if required scope is present and get user_email from token
    Create local admin account if not yet present
    """
    @staticmethod  # noqa: C901
    def authenticate(request):
        USER_NOT_AUTHORIZED = "User {} is not authorized"

        scope = required_scope = 'SIG/ALL'
        if hasattr(request, "is_authorized_for") and request.is_authorized_for(required_scope):
            user_email = request.get_token_subject.lower()

            if user_email == "always_ok":
                user_email = settings.TEST_LOGIN
        else:
            raise exceptions.AuthenticationFailed("No token or required scope")
        user = cache.get(user_email)
        if user == 'None':
            raise exceptions.AuthenticationFailed(USER_NOT_AUTHORIZED.format(user_email))

        if not user:
            login_valid = (settings.ADMIN_LOGIN == user_email)
            if login_valid:
                try:
                    user = User.objects.get(username=user_email)
                except User.DoesNotExist:
                    # Create a new user. There's no need to set a password
                    # because only the password from settings.py is checked.
                    user = User(email=user_email, username=user_email)
                    user.is_staff = True
                    user.is_superuser = True
                    user.save()
            else:
                try:
                    user = User.objects.get(username=user_email)
                except User.DoesNotExist:
                    # wait 5 minutes after users have been changed
                    cache.set(user_email, 'None', 5 * 60)
                    raise exceptions.AuthenticationFailed(USER_NOT_AUTHORIZED.format(user_email))
            cache.set(user_email, user, 5 * 60)  # wait 5 minutes after users have been changed
        if user is None:
            user = AnonymousUser()
            scope = ""
        return user, scope

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        return 'Bearer realm="signals"'
