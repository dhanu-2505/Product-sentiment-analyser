from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SourceDefinition:
    code: str
    name: str
    base_url: str
    live_connector_configured: bool = False


class BaseSource(ABC):
    definition: SourceDefinition

    @abstractmethod
    def fetch_product(self, query: str) -> dict[str, Any]:
        raise NotImplementedError


class UnavailableSource(BaseSource):
    def __init__(self, definition: SourceDefinition):
        self.definition = definition

    def fetch_product(self, query: str) -> dict[str, Any]:
        return {
            "source": self.definition.code,
            "status": "unavailable",
            "checked": False,
            "message": "Live data unavailable for this source.",
        }
