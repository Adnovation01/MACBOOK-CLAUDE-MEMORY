from unittest.mock import patch, MagicMock
import requests

FAKE_DDG_HTML = """
<html><body>
  <a class="result__a" href="https://austindental.com">Austin Dental Care</a>
  <a class="result__a" href="https://smilesalon.com">Smile Salon Austin</a>
  <a class="result__a" href="https://yelp.com/biz/test">Yelp listing</a>
</body></html>
"""

FAKE_BING_HTML = """
<html><body>
  <li class="b_algo"><h2><a href="https://bestdentist.com">Best Dentist Austin</a></h2></li>
</body></html>
"""

FAKE_GOOGLE_HTML = """
<html><body>
  <div class="g"><a href="https://austindental.com"><h3>Austin Dental</h3></a></div>
</body></html>
"""

def _mock_response(html):
    m = MagicMock()
    m.text = html
    m.status_code = 200
    return m

def test_duckduckgo_returns_leads(monkeypatch):
    monkeypatch.setattr(requests, 'get', lambda *a, **kw: _mock_response(FAKE_DDG_HTML))
    from src.plugins.duckduckgo_plugin import DuckDuckGoPlugin
    plugin = DuckDuckGoPlugin()
    leads = plugin.search("dentist", "Austin, TX", max_leads=5)
    assert len(leads) >= 1
    assert any(l.website == "https://austindental.com" for l in leads)

def test_duckduckgo_filters_blocked_domains(monkeypatch):
    monkeypatch.setattr(requests, 'get', lambda *a, **kw: _mock_response(FAKE_DDG_HTML))
    from src.plugins.duckduckgo_plugin import DuckDuckGoPlugin
    plugin = DuckDuckGoPlugin()
    leads = plugin.search("dentist", "Austin, TX", max_leads=10)
    assert not any('yelp.' in l.website for l in leads)

def test_bing_returns_leads(monkeypatch):
    monkeypatch.setattr(requests, 'get', lambda *a, **kw: _mock_response(FAKE_BING_HTML))
    from src.plugins.bing_search_plugin import BingSearchPlugin
    plugin = BingSearchPlugin()
    leads = plugin.search("dentist", "Austin, TX", max_leads=5)
    assert len(leads) >= 1
    assert leads[0].website == "https://bestdentist.com"

def test_search_plugins_available():
    from src.plugins.duckduckgo_plugin import DuckDuckGoPlugin
    from src.plugins.bing_search_plugin import BingSearchPlugin
    from src.plugins.google_search_plugin import GoogleSearchPlugin
    assert DuckDuckGoPlugin().is_available() is True
    assert BingSearchPlugin().is_available() is True
    assert GoogleSearchPlugin().is_available() is True
