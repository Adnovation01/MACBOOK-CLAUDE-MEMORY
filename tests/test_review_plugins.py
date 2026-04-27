import requests
from unittest.mock import MagicMock
from src.plugins.trustpilot_plugin import TrustpilotPlugin
from src.plugins.healthgrades_plugin import HealthgradesPlugin
from src.plugins.angi_plugin import AngiPlugin
from src.plugins.thumbtack_plugin import ThumbtackPlugin
from src.plugins.opencorporates_plugin import OpenCorporatesPlugin
from src.plugins.state_registry_plugin import StateRegistryPlugin

ALL_PLUGINS = [
    TrustpilotPlugin(), HealthgradesPlugin(), AngiPlugin(),
    ThumbtackPlugin(), OpenCorporatesPlugin(), StateRegistryPlugin()
]

def test_all_review_plugins_available():
    for plugin in ALL_PLUGINS:
        assert plugin.is_available() is True

def test_all_review_plugin_names():
    names = {p.name for p in ALL_PLUGINS}
    assert names == {'trustpilot', 'healthgrades', 'angi', 'thumbtack', 'opencorporates', 'state_registry'}

def test_all_return_empty_on_network_failure(monkeypatch):
    monkeypatch.setattr(requests, 'get', lambda *a, **kw: (_ for _ in ()).throw(Exception("network")))
    for plugin in ALL_PLUGINS:
        result = plugin.search("dentist", "Austin, TX", max_leads=5)
        assert result == [], f"{plugin.name} should return [] on error"

def test_state_registry_skips_unsupported_state(monkeypatch):
    mock_resp = MagicMock()
    mock_resp.text = "<html></html>"
    monkeypatch.setattr(requests, 'get', lambda *a, **kw: mock_resp)
    plugin = StateRegistryPlugin()
    result = plugin.search("dentist", "Austin, WY", max_leads=5)
    assert result == []
