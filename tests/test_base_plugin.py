from src.plugins.base_plugin import BasePlugin
from src.models.lead import Lead
from typing import List

class MinimalPlugin(BasePlugin):
    name = "minimal"
    def search(self, keyword, location, max_leads) -> List[Lead]:
        return []

def test_default_health_check_returns_healthy():
    p = MinimalPlugin()
    result = p.health_check()
    assert result["status"] == "healthy"
    assert result["error"] is None

def test_health_check_returns_dict_with_required_keys():
    p = MinimalPlugin()
    result = p.health_check()
    assert "status" in result
    assert "error" in result
