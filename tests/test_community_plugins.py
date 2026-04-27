import os
from src.session_manager import SessionManager
from src.plugins.twitter_plugin import TwitterPlugin
from src.plugins.youtube_plugin import YouTubePlugin
from src.plugins.reddit_plugin import RedditPlugin

def test_twitter_unavailable_without_session(tmp_path, monkeypatch):
    monkeypatch.setattr(SessionManager, 'SESSION_DIR', tmp_path)
    plugin = TwitterPlugin(SessionManager())
    assert plugin.is_available() is False

def test_twitter_returns_empty_when_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(SessionManager, 'SESSION_DIR', tmp_path)
    plugin = TwitterPlugin(SessionManager())
    assert plugin.search("dentist", "Austin, TX", max_leads=5) == []

def test_youtube_always_available():
    assert YouTubePlugin().is_available() is True

def test_youtube_returns_list_on_failure(monkeypatch):
    import requests
    monkeypatch.setattr(requests, 'get', lambda *a, **kw: (_ for _ in ()).throw(Exception("network")))
    assert YouTubePlugin().search("dentist", "Austin, TX", max_leads=5) == []

def test_reddit_unavailable_without_credentials(monkeypatch):
    monkeypatch.delenv('REDDIT_CLIENT_ID', raising=False)
    monkeypatch.delenv('REDDIT_CLIENT_SECRET', raising=False)
    assert RedditPlugin().is_available() is False

def test_reddit_search_returns_empty():
    plugin = RedditPlugin()
    assert plugin.search("dentist", "Austin, TX", max_leads=5) == []
