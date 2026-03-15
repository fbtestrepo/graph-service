from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GRAPH_SERVICE_", extra="ignore")

    mongodb_uri: str = Field(default="mongodb://localhost:27017", description="MongoDB connection URI")
    mongodb_database: str = Field(default="graph_service", description="MongoDB database name")

    ldap_server_uri: str = Field(default="ldap://localhost:389", description="LDAP server URI")
    ldap_bind_dn: str = Field(default="", description="LDAP bind DN (optional)")
    ldap_bind_password: str = Field(default="", description="LDAP bind password (optional)")


def load_settings() -> Settings:
    return Settings()
