from _typeshed import Incomplete
from django.utils.deprecation import MiddlewareMixin
from mozilla_django_oidc.auth import OIDCAuthenticationBackend as OIDCAuthenticationBackend
from mozilla_django_oidc.utils import absolutify as absolutify, add_state_and_nonce_to_session as add_state_and_nonce_to_session, import_from_settings as import_from_settings

LOGGER: Incomplete

class SessionRefresh(MiddlewareMixin):
    OIDC_EXEMPT_URLS: Incomplete
    OIDC_OP_AUTHORIZATION_ENDPOINT: Incomplete
    OIDC_RP_CLIENT_ID: Incomplete
    OIDC_STATE_SIZE: Incomplete
    OIDC_AUTHENTICATION_CALLBACK_URL: Incomplete
    OIDC_RP_SCOPES: Incomplete
    OIDC_USE_NONCE: Incomplete
    OIDC_NONCE_SIZE: Incomplete
    def __init__(self, get_response) -> None: ...
    @staticmethod
    def get_settings(attr, *args): ...
    def exempt_urls(self): ...
    def exempt_url_patterns(self): ...
    def is_refreshable_url(self, request): ...
    def process_request(self, request): ...
