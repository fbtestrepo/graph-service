from __future__ import annotations

from fastapi import APIRouter, FastAPI

from src.adapters.inbound.api.routers.application_architectures import (
    router as application_architectures_router,
)
from src.adapters.inbound.api.routers.component_validation import router as component_validation_router
from src.adapters.inbound.api.routers.components import router as components_router
from src.adapters.inbound.api.routers.health import router as health_router
from src.adapters.inbound.api.routers.micro_affinity_groups import (
    router as micro_affinity_groups_router,
)
from src.adapters.outbound.ldap.client import create_ldap_connection
from src.adapters.outbound.ldap.identity_provider import LdapIdentityProvider
from src.adapters.outbound.mongodb.application_architecture_repository import (
    MongoApplicationArchitectureRepository,
)
from src.adapters.outbound.mongodb.client import create_mongo_client
from src.adapters.outbound.mongodb.component_node_repository import MongoComponentNodeRepository
from src.adapters.outbound.mongodb.component_payload_repository import MongoComponentPayloadRepository
from src.adapters.outbound.mongodb.graph_repository import MongoGraphRepository
from src.adapters.outbound.mongodb.micro_affinity_group_repository import (
    MongoMicroAffinityGroupRepository,
)
from src.adapters.outbound.mongodb.micro_affinity_group_processed_repository import (
    MongoMicroAffinityGroupProcessedRepository,
)
from src.adapters.outbound.mongodb.transaction_manager import MongoTransactionManager
from src.infrastructure.config.settings import load_settings
from src.infrastructure.errors.handlers import register_exception_handlers
from src.infrastructure.errors.validation import register_validation_error_handlers


def create_app() -> FastAPI:
    app = FastAPI(title="Dependency Graph Service")
    v1_router = APIRouter(prefix="/v1")

    register_validation_error_handlers(app)
    register_exception_handlers(app)

    app.include_router(health_router)
    v1_router.include_router(component_validation_router)
    v1_router.include_router(components_router)
    v1_router.include_router(application_architectures_router)
    v1_router.include_router(micro_affinity_groups_router)
    app.include_router(v1_router)

    settings = load_settings()
    app.state.settings = settings

    @app.on_event("startup")
    async def _startup() -> None:
        if not hasattr(app.state, "mongo_client"):
            mongo_client = create_mongo_client(settings.mongodb_uri)
            app.state.mongo_client = mongo_client

        if not hasattr(app.state, "mongo_db"):
            app.state.mongo_db = app.state.mongo_client[settings.mongodb_database]

        if not hasattr(app.state, "graph_repository"):
            app.state.graph_repository = MongoGraphRepository(app.state.mongo_db)

        if not hasattr(app.state, "component_payload_repository"):
            app.state.component_payload_repository = MongoComponentPayloadRepository(app.state.mongo_db)

        if not hasattr(app.state, "component_node_repository"):
            app.state.component_node_repository = MongoComponentNodeRepository(app.state.mongo_db)

        if not hasattr(app.state, "application_architecture_repository"):
            app.state.application_architecture_repository = MongoApplicationArchitectureRepository(
                app.state.mongo_db
            )

        if not hasattr(app.state, "micro_affinity_group_repository"):
            app.state.micro_affinity_group_repository = MongoMicroAffinityGroupRepository(
                app.state.mongo_db
            )

        if not hasattr(app.state, "micro_affinity_group_processed_repository"):
            app.state.micro_affinity_group_processed_repository = (
                MongoMicroAffinityGroupProcessedRepository(app.state.mongo_db)
            )

        if not hasattr(app.state, "transaction_manager"):
            app.state.transaction_manager = MongoTransactionManager(app.state.mongo_client)

        if not hasattr(app.state, "ldap_connection"):
            ldap_conn = create_ldap_connection(
                server_uri=settings.ldap_server_uri,
                bind_dn=settings.ldap_bind_dn,
                bind_password=settings.ldap_bind_password,
            )
            app.state.ldap_connection = ldap_conn

        if not hasattr(app.state, "identity_provider"):
            app.state.identity_provider = LdapIdentityProvider(app.state.ldap_connection)

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


