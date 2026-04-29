from unittest.mock import patch, MagicMock
import pytest


def _make_response(status_code):
    r = MagicMock()
    r.status_code = status_code
    return r


def test_duckduckgo_health_check_healthy():
    from src.plugins.duckduckgo_plugin import DuckDuckGoPlugin
    p = DuckDuckGoPlugin()
    with patch('requests.head', return_value=_make_response(200)):
        result = p.health_check()
    assert result['status'] == 'healthy'
    assert result['error'] is None


def test_duckduckgo_health_check_failed_on_500():
    from src.plugins.duckduckgo_plugin import DuckDuckGoPlugin
    p = DuckDuckGoPlugin()
    with patch('requests.head', return_value=_make_response(503)):
        result = p.health_check()
    assert result['status'] == 'failed'
    assert '503' in result['error']


def test_duckduckgo_health_check_failed_on_exception():
    from src.plugins.duckduckgo_plugin import DuckDuckGoPlugin
    p = DuckDuckGoPlugin()
    with patch('requests.head', side_effect=Exception('connection refused')):
        result = p.health_check()
    assert result['status'] == 'failed'
    assert 'connection refused' in result['error']


def test_yelp_health_check_healthy():
    from src.plugins.yelp_plugin import YelpPlugin
    p = YelpPlugin()
    with patch('requests.head', return_value=_make_response(200)):
        result = p.health_check()
    assert result['status'] == 'healthy'


def test_google_maps_health_check_healthy():
    from src.plugins.google_maps_plugin import GoogleMapsPlugin
    p = GoogleMapsPlugin()
    with patch('requests.head', return_value=_make_response(200)):
        result = p.health_check()
    assert result['status'] == 'healthy'


def test_facebook_health_check_degraded_when_no_session():
    from src.plugins.facebook_plugin import FacebookPlugin
    from src.session_manager import SessionManager
    sm = MagicMock(spec=SessionManager)
    sm.is_authenticated.return_value = False
    p = FacebookPlugin(sm)
    result = p.health_check()
    assert result['status'] == 'degraded'
    assert 'credentials' in result['error'].lower()


def test_facebook_health_check_healthy_when_session_exists():
    from src.plugins.facebook_plugin import FacebookPlugin
    from src.session_manager import SessionManager
    sm = MagicMock(spec=SessionManager)
    sm.is_authenticated.return_value = True
    p = FacebookPlugin(sm)
    result = p.health_check()
    assert result['status'] == 'healthy'
    assert result['error'] is None
