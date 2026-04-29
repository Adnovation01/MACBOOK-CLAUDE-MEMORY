import json
import os
import pytest
from unittest.mock import MagicMock
from src.plugins.base_plugin import BasePlugin
from src.models.lead import Lead


def make_plugin(name, health_result, leads=None):
    p = MagicMock(spec=BasePlugin)
    p.name = name
    p.health_check.return_value = health_result
    p.search.return_value = leads or [Lead(business_name="Test", city="NYC", state="NY", sources=[name])]
    return p


def test_lightweight_check_marks_healthy_plugin(tmp_path):
    from src.plugin_health_monitor import PluginHealthMonitor
    p = make_plugin("duckduckgo", {"status": "healthy", "error": None})
    monitor = PluginHealthMonitor([p], cache_path=str(tmp_path / "health.json"))
    result = monitor.run_lightweight_check()
    assert result["duckduckgo"]["status"] == "healthy"
    assert result["duckduckgo"]["error"] is None


def test_lightweight_check_marks_failed_plugin(tmp_path):
    from src.plugin_health_monitor import PluginHealthMonitor
    p = make_plugin("yelp", {"status": "failed", "error": "HTTP 403"})
    monitor = PluginHealthMonitor([p], cache_path=str(tmp_path / "health.json"))
    result = monitor.run_lightweight_check()
    assert result["yelp"]["status"] == "failed"
    assert "403" in result["yelp"]["error"]


def test_lightweight_check_marks_degraded_plugin(tmp_path):
    from src.plugin_health_monitor import PluginHealthMonitor
    p = make_plugin("facebook", {"status": "degraded", "error": "missing credentials"})
    monitor = PluginHealthMonitor([p], cache_path=str(tmp_path / "health.json"))
    result = monitor.run_lightweight_check()
    assert result["facebook"]["status"] == "degraded"


def test_cache_is_persisted_to_file(tmp_path):
    from src.plugin_health_monitor import PluginHealthMonitor
    cache_file = str(tmp_path / "health.json")
    p = make_plugin("bing_search", {"status": "healthy", "error": None})
    monitor = PluginHealthMonitor([p], cache_path=cache_file)
    monitor.run_lightweight_check()
    assert os.path.exists(cache_file)
    with open(cache_file) as f:
        data = json.load(f)
    assert "bing_search" in data


def test_cache_ttl_not_rechecked_within_ttl(tmp_path):
    from src.plugin_health_monitor import PluginHealthMonitor
    p = make_plugin("duckduckgo", {"status": "healthy", "error": None})
    monitor = PluginHealthMonitor([p], cache_path=str(tmp_path / "health.json"))
    monitor.run_lightweight_check()
    monitor.run_lightweight_check()
    assert p.health_check.call_count == 1


def test_get_healthy_plugin_names(tmp_path):
    from src.plugin_health_monitor import PluginHealthMonitor
    p1 = make_plugin("duckduckgo", {"status": "healthy", "error": None})
    p2 = make_plugin("yelp", {"status": "failed", "error": "403"})
    p3 = make_plugin("facebook", {"status": "degraded", "error": "no creds"})
    monitor = PluginHealthMonitor([p1, p2, p3], cache_path=str(tmp_path / "health.json"))
    monitor.run_lightweight_check()
    names = monitor.get_healthy_plugin_names()
    assert names == ["duckduckgo"]
    assert "yelp" not in names
    assert "facebook" not in names


def test_get_summary(tmp_path):
    from src.plugin_health_monitor import PluginHealthMonitor
    p1 = make_plugin("a", {"status": "healthy", "error": None})
    p2 = make_plugin("b", {"status": "failed", "error": "err"})
    p3 = make_plugin("c", {"status": "degraded", "error": "creds"})
    monitor = PluginHealthMonitor([p1, p2, p3], cache_path=str(tmp_path / "health.json"))
    monitor.run_lightweight_check()
    summary = monitor.get_summary()
    assert summary["healthy"] == 1
    assert summary["failed"] == 1
    assert summary["degraded"] == 1
