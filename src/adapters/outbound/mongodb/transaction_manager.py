from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from pymongo import MongoClient

from src.core.ports.transaction_manager import TransactionManager


ResultT = TypeVar("ResultT")


class MongoTransactionManager(TransactionManager):
    def __init__(self, client: MongoClient):
        self._client = client

    def execute(self, operation: Callable[[object], ResultT]) -> ResultT:
        with self._client.start_session() as session:
            return session.with_transaction(lambda session: operation(session))