from unittest.mock import patch, MagicMock
from src.plugins.yellowpages_plugin import YellowPagesPlugin
from src.plugins.google_maps_plugin import GoogleMapsPlugin

def test_yellowpages_available():
    plugin = YellowPagesPlugin()
    # availability depends on playwright being installed
    assert isinstance(plugin.is_available(), bool)

def test_yellowpages_returns_empty_when_unavailable():
    plugin = YellowPagesPlugin()
    if plugin.is_available():
        return  # skip — playwright installed, unavailability path not reachable
    results = plugin.search("dentist", "Austin, TX", max_leads=5)
    assert results == []

def test_google_maps_available():
    plugin = GoogleMapsPlugin()
    assert isinstance(plugin.is_available(), bool)

def test_yellowpages_name_set():
    assert YellowPagesPlugin.name == "yellowpages"

def test_google_maps_name_set():
    assert GoogleMapsPlugin.name == "google_maps"
