from abc import ABC, abstractmethod
from typing import List
from src.models.lead import Lead

class BasePlugin(ABC):
    name: str = ""
    requires_auth: bool = False
    rate_limit_seconds: float = 2.0

    @abstractmethod
    def search(self, keyword: str, location: str, max_leads: int) -> List[Lead]:
        pass

    def is_available(self) -> bool:
        return True
