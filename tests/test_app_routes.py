import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app as flask_app

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c

def test_login_page_renders(client):
    resp = client.get('/login')
    assert resp.status_code == 200
    assert b'login' in resp.data.lower()

def test_unauthenticated_dashboard_redirects(client):
    resp = client.get('/')
    assert resp.status_code in (302, 308)

def test_unauthenticated_scraper_redirects(client):
    resp = client.get('/scraper')
    assert resp.status_code in (302, 308)

def test_unauthenticated_leads_redirects(client):
    resp = client.get('/leads')
    assert resp.status_code in (302, 308)

def test_unauthenticated_settings_redirects(client):
    resp = client.get('/settings')
    assert resp.status_code in (302, 308)

def test_health_endpoint_redirects_unauthenticated(client):
    resp = client.get('/api/plugins/health')
    assert resp.status_code in (302, 308)

def test_diagnose_endpoint_redirects_unauthenticated(client):
    resp = client.post('/api/plugins/diagnose')
    assert resp.status_code in (302, 308)
