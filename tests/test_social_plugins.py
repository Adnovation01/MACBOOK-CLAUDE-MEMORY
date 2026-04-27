import json
from pathlib import Path
from src.session_manager import SessionManager
from src.plugins.facebook_plugin import FacebookPlugin
from src.plugins.instagram_plugin import InstagramPlugin
from src.plugins.linkedin_plugin import LinkedInPlugin

def test_facebook_unavailable_without_session(tmp_path, monkeypatch):
    monkeypatch.setattr(SessionManager, 'SESSION_DIR', tmp_path)
    plugin = FacebookPlugin(SessionManager())
    assert plugin.is_available() is False

def test_instagram_unavailable_without_session(tmp_path, monkeypatch):
    monkeypatch.setattr(SessionManager, 'SESSION_DIR', tmp_path)
    plugin = InstagramPlugin(SessionManager())
    assert plugin.is_available() is False

def test_linkedin_unavailable_without_session(tmp_path, monkeypatch):
    monkeypatch.setattr(SessionManager, 'SESSION_DIR', tmp_path)
    plugin = LinkedInPlugin(SessionManager())
    assert plugin.is_available() is False

def test_social_plugins_return_empty_when_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(SessionManager, 'SESSION_DIR', tmp_path)
    sm = SessionManager()
    for plugin in [FacebookPlugin(sm), InstagramPlugin(sm), LinkedInPlugin(sm)]:
        assert plugin.search("dentist", "Austin, TX", max_leads=5) == []

def test_social_plugins_names():
    sm = SessionManager()
    assert FacebookPlugin(sm).name == "facebook"
    assert InstagramPlugin(sm).name == "instagram"
    assert LinkedInPlugin(sm).name == "linkedin"
