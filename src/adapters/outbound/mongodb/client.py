from __future__ import annotations

from pymongo import MongoClient


def create_mongo_client(mongodb_uri: str) -> MongoClient:
    return MongoClient(mongodb_uri)
