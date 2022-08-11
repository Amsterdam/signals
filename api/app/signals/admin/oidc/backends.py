# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Delta10 B.V.
from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class AuthenticationBackend(OIDCAuthenticationBackend):
    def filter_users_by_claims(self, claims):
        email = claims.get('email')
        if not email:
            return self.UserModel.objects.none()

        return self.UserModel.objects.filter(username__iexact=email)

    def create_user(self, claims):
        return None # do not create users when they do not exist in the database

    def update_user(self, user, claims):
        return user  # do not update any attributes in the database based on claims
