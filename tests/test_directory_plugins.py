from src.plugins.yelp_plugin import YelpPlugin
from src.plugins.bbb_plugin import BBBPlugin
from src.plugins.manta_plugin import MantaPlugin
from src.plugins.superpages_plugin import SuperpagesPlugin
from src.plugins.hotfrog_plugin import HotfrogPlugin
from src.plugins.whitepages_plugin import WhitepagesPlugin
from src.plugins.foursquare_plugin import FoursquarePlugin
from src.plugins.cylex_plugin import CylexPlugin
from src.plugins.clutch_plugin import ClutchPlugin
from src.plugins.brownbook_plugin import BrownbookPlugin

ALL_PLUGINS = [
    YelpPlugin(), BBBPlugin(), MantaPlugin(), SuperpagesPlugin(), HotfrogPlugin(),
    WhitepagesPlugin(), FoursquarePlugin(), CylexPlugin(), ClutchPlugin(), BrownbookPlugin()
]

def test_all_directory_plugins_available():
    for plugin in ALL_PLUGINS:
        assert plugin.is_available() is True, f"{plugin.name} should be available"

def test_all_directory_plugins_have_name():
    names = {p.name for p in ALL_PLUGINS}
    expected = {'yelp', 'bbb', 'manta', 'superpages', 'hotfrog', 'whitepages', 'foursquare', 'cylex', 'clutch', 'brownbook'}
    assert names == expected

def test_all_plugins_return_list_on_network_failure(monkeypatch):
    import requests
    monkeypatch.setattr(requests, 'get', lambda *a, **kw: (_ for _ in ()).throw(Exception("network error")))
    for plugin in ALL_PLUGINS:
        result = plugin.search("dentist", "Austin, TX", max_leads=5)
        assert isinstance(result, list), f"{plugin.name} should return list on error"
        assert result == [], f"{plugin.name} should return empty list on error"

def test_plugins_set_correct_source(monkeypatch):
    import requests
    from unittest.mock import MagicMock
    mock_resp = MagicMock()
    mock_resp.text = "<html><body></body></html>"
    monkeypatch.setattr(requests, 'get', lambda *a, **kw: mock_resp)
    for plugin in ALL_PLUGINS:
        results = plugin.search("dentist", "Austin, TX", max_leads=5)
        for lead in results:
            assert plugin.name in lead.sources
