from __future__ import annotations


class AuthorizationDenied(Exception):
    def __init__(self, detail: str = "Authorization denied"):
        super().__init__(detail)
        self.detail = detail
