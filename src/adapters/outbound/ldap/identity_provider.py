from __future__ import annotations

from ldap3 import Connection

from src.core.exceptions.authentication_failed import AuthenticationFailed
from src.core.exceptions.authorization_denied import AuthorizationDenied
from src.core.ports.identity_provider import IdentityProvider


class LdapIdentityProvider(IdentityProvider):
    def __init__(self, connection: Connection):
        self._connection = connection

    def authenticate(self, bearer_token: str) -> str:
        if not bearer_token:
            raise AuthenticationFailed("Missing bearer token")
        # Skeleton behavior: treat any non-empty token as authenticated.
        return "subject"

    def ensure_authorized(self, subject: str, required_role: str) -> None:
        if not required_role:
            return
        # Skeleton behavior: authorization is not implemented.
        raise AuthorizationDenied("Authorization not implemented in skeleton")
