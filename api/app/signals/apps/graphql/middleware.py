from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed

from signals.auth.backend import JWTAuthBackend


class AuthenticationMiddleware:
    def resolve(self, next, root, info, **args):
        try:
            info.context.user, _ = JWTAuthBackend.authenticate(info.context)
        except AuthenticationFailed:
            info.context.user = AnonymousUser

        promise = next(root, info, **args)
        return promise
