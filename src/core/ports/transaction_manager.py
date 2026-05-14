from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar


ResultT = TypeVar("ResultT")


class TransactionManager(ABC):
    @abstractmethod
    def execute(self, operation: Callable[[Any], ResultT]) -> ResultT:
        """Execute an operation inside one transaction-bound session."""

        raise NotImplementedError