from __future__ import annotations

from ldap3 import Connection, Server


def create_ldap_connection(
    server_uri: str,
    bind_dn: str,
    bind_password: str,
) -> Connection:
    server = Server(server_uri)
    # Intentionally does not auto-bind; binding is adapter responsibility.
    return Connection(server, user=bind_dn or None, password=bind_password or None, auto_bind=False)
