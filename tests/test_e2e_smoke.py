"""
Smoke test: runs the orchestrator with 2 fast plugins (DuckDuckGo + Bing),
verifies leads are returned in the correct schema, and verifies the sequence
is scheduled correctly. Does not hit real network or Gmail SMTP.
"""
import sqlite3
import requests
from unittest.mock import MagicMock
from src.plugins.duckduckgo_plugin import DuckDuckGoPlugin
from src.plugins.bing_search_plugin import BingSearchPlugin
from src.scraper_orchestrator import ScraperOrchestrator
from src.email_sequence_manager import EmailSequenceManager
from src.models.lead import Lead

FAKE_HTML = '<html><body><a class="result__a" href="https://austindental.com">Austin Dental Care</a></body></html>'

def test_full_pipeline_smoke(monkeypatch):
    mock_resp = MagicMock()
    mock_resp.text = FAKE_HTML
    monkeypatch.setattr(requests, 'get', lambda *a, **kw: mock_resp)

    plugins = [DuckDuckGoPlugin(), BingSearchPlugin()]
    orch = ScraperOrchestrator(plugins=plugins)
    leads = orch.scrape("dentist", "Austin, TX", max_leads=5)

    assert isinstance(leads, list)
    for lead in leads:
        assert isinstance(lead, Lead)
        assert lead.sources  # at least one source assigned

def test_sequence_scheduled_per_lead_with_email(tmp_path):
    db = str(tmp_path / 'smoke.db')
    mgr = EmailSequenceManager(db_path=db)
    leads = [
        Lead(business_name="Test A", email="a@test.com", city="Austin", state="TX"),
        Lead(business_name="No Email", email="", city="Austin", state="TX"),
        Lead(business_name="Test B", email="b@test.com", city="Austin", state="TX"),
    ]
    for lead in leads:
        mgr.schedule(lead)
    with sqlite3.connect(db) as conn:
        count = conn.execute("SELECT count(*) FROM email_sequences").fetchone()[0]
    assert count == 14  # 2 leads with email x 7 emails each

def test_plugin_factory_builds_all_plugins():
    from src.plugins.plugin_factory import build_plugins
    plugins = build_plugins()
    assert len(plugins) == 27
    names = {p.name for p in plugins}
    assert 'duckduckgo' in names
    assert 'facebook' in names
    assert 'state_registry' in names

def test_lead_schema_all_fields_serializable():
    lead = Lead(
        business_name="Test Biz", email="t@t.com", city="Austin", state="TX",
        hook_1="Your reviews show wait time complaints",
        hook_2="Competitor has 4.9 stars vs your 3.8",
        intent_score=40,
        pain_points=["long waits", "hard to book"],
        website_issues=["no_contact_or_booking_form"],
        sources=["yelp", "google_maps"]
    )
    d = lead.to_dict()
    assert d['intent_score'] == 40
    assert d['hook_1'] == "Your reviews show wait time complaints"
    assert len(d['sources']) == 2
    assert 'scraped_at' in d
