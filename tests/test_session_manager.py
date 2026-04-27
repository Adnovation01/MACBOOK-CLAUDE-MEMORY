import json
from pathlib import Path
from src.session_manager import SessionManager

def test_load_missing_session_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(SessionManager, 'SESSION_DIR', tmp_path)
    sm = SessionManager()
    assert sm.get_cookies('facebook') is None

def test_load_existing_session(tmp_path, monkeypatch):
    monkeypatch.setattr(SessionManager, 'SESSION_DIR', tmp_path)
    cookies = [{"name": "session", "value": "abc123"}]
    (tmp_path / 'facebook.json').write_text(json.dumps(cookies))
    sm = SessionManager()
    loaded = sm.get_cookies('facebook')
    assert loaded == cookies

def test_is_authenticated_false_when_no_session(tmp_path, monkeypatch):
    monkeypatch.setattr(SessionManager, 'SESSION_DIR', tmp_path)
    sm = SessionManager()
    assert sm.is_authenticated('instagram') is False

def test_is_authenticated_true_when_session_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(SessionManager, 'SESSION_DIR', tmp_path)
    (tmp_path / 'linkedin.json').write_text(json.dumps([{"name": "li_at", "value": "token"}]))
    sm = SessionManager()
    assert sm.is_authenticated('linkedin') is True
