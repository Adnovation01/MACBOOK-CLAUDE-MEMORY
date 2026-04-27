from unittest.mock import MagicMock
from src.scraper_orchestrator import ScraperOrchestrator
from src.models.lead import Lead
from src.plugins.base_plugin import BasePlugin

def make_plugin(name, leads):
    p = MagicMock(spec=BasePlugin)
    p.name = name
    p.is_available.return_value = True
    p.search.return_value = leads
    return p

def test_orchestrator_merges_results_from_all_plugins():
    p1 = make_plugin("yelp", [Lead(business_name="Smith Dental", city="Austin", state="TX", sources=["yelp"], email="a@b.com")])
    p2 = make_plugin("google_maps", [Lead(business_name="Smith Dental", city="Austin", state="TX", sources=["google_maps"], phone="555-1234")])
    orch = ScraperOrchestrator(plugins=[p1, p2])
    results = orch.scrape("dentist", "Austin, TX", max_leads=10)
    assert len(results) == 1
    assert results[0].email == "a@b.com"
    assert results[0].phone == "555-1234"

def test_unavailable_plugin_is_skipped():
    p1 = make_plugin("yelp", [Lead(business_name="Good Biz", city="NYC", state="NY", sources=["yelp"])])
    p2 = make_plugin("broken", [])
    p2.is_available.return_value = False
    orch = ScraperOrchestrator(plugins=[p1, p2])
    results = orch.scrape("dentist", "NYC, NY", max_leads=10)
    assert any(r.business_name == "Good Biz" for r in results)
    p2.search.assert_not_called()

def test_intent_score_assigned():
    lead = Lead(
        business_name="Test Biz", city="Austin", state="TX",
        sources=["yelp"],
        recent_negative_reviews=["Terrible service"],
        website_issues=["no_contact_or_booking_form"]
    )
    p1 = make_plugin("yelp", [lead])
    orch = ScraperOrchestrator(plugins=[p1])
    results = orch.scrape("dentist", "Austin, TX", max_leads=10)
    assert results[0].intent_score > 0

def test_empty_plugins_returns_empty():
    orch = ScraperOrchestrator(plugins=[])
    results = orch.scrape("dentist", "Austin, TX", max_leads=10)
    assert results == []
