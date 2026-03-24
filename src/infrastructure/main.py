from __future__ import annotations

from fastapi import FastAPI

from src.adapters.inbound.api.routers.component_validation import router as component_validation_router
from src.adapters.inbound.api.routers.components import router as components_router
from src.adapters.inbound.api.routers.health import router as health_router
from src.adapters.outbound.ldap.client import create_ldap_connection
from src.adapters.outbound.ldap.identity_provider import LdapIdentityProvider
from src.adapters.outbound.mongodb.client import create_mongo_client
from src.adapters.outbound.mongodb.component_payload_repository import MongoComponentPayloadRepository
from src.adapters.outbound.mongodb.graph_repository import MongoGraphRepository
from src.infrastructure.config.settings import load_settings
from src.infrastructure.errors.handlers import register_exception_handlers
from src.infrastructure.errors.validation import register_validation_error_handlers


def create_app() -> FastAPI:
    app = FastAPI(title="Dependency Graph Service")

    register_validation_error_handlers(app)
    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(component_validation_router)
    app.include_router(components_router)

    settings = load_settings()
    app.state.settings = settings

    @app.on_event("startup")
    async def _startup() -> None:
        mongo_client = create_mongo_client(settings.mongodb_uri)
        app.state.mongo_client = mongo_client
        app.state.mongo_db = mongo_client[settings.mongodb_database]
        app.state.graph_repository = MongoGraphRepository(app.state.mongo_db)
        app.state.component_payload_repository = MongoComponentPayloadRepository(app.state.mongo_db)

        ldap_conn = create_ldap_connection(
            server_uri=settings.ldap_server_uri,
            bind_dn=settings.ldap_bind_dn,
            bind_password=settings.ldap_bind_password,
        )
        app.state.ldap_connection = ldap_conn
        app.state.identity_provider = LdapIdentityProvider(ldap_conn)

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        mongo_client = getattr(app.state, "mongo_client", None)
        if mongo_client is not None:
            mongo_client.close()

        ldap_conn = getattr(app.state, "ldap_connection", None)
        if ldap_conn is not None:
            try:
                ldap_conn.unbind()
            except Exception:
                # Best-effort shutdown.
                pass

    return app


