# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 - 2024 Delta10 B.V., Gemeente Amsterdam
from amsterdam_django_oidc import OIDCAuthenticationBackend


class AuthenticationBackend(OIDCAuthenticationBackend):
    def filter_users_by_claims(self, claims):
        email = claims.get('email')
        if not email:
            return self.UserModel.objects.none()

        return self.UserModel.objects.filter(username__iexact=email)
