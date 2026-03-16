from __future__ import annotations


class AuthenticationFailed(Exception):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(detail)
        self.detail = detail
