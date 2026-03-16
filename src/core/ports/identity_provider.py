from __future__ import annotations

from abc import ABC, abstractmethod

from src.core.exceptions.authentication_failed import AuthenticationFailed
from src.core.exceptions.authorization_denied import AuthorizationDenied


class IdentityProvider(ABC):
    @abstractmethod
    def authenticate(self, bearer_token: str) -> str:
        """Returns a subject identifier or raises AuthenticationFailed."""

    @abstractmethod
    def ensure_authorized(self, subject: str, required_role: str) -> None:
        """Raises AuthorizationDenied when subject lacks required_role."""
