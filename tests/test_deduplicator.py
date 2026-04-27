import pytest
from src.deduplicator import Deduplicator
from src.models.lead import Lead

def test_exact_website_match_deduplicates():
    leads = [
        Lead(business_name="Smith Dental", website="https://smithdental.com", city="Austin", state="TX", sources=["yelp"], email="a@b.com"),
        Lead(business_name="Smith Dental Care", website="https://smithdental.com", city="Austin", state="TX", sources=["google_maps"], phone="555-1234"),
    ]
    d = Deduplicator(total_plugins=27)
    result = d.deduplicate(leads)
    assert len(result) == 1
    assert result[0].email == "a@b.com"
    assert result[0].phone == "555-1234"
    assert set(result[0].sources) == {"yelp", "google_maps"}

def test_fuzzy_name_match_deduplicates():
    leads = [
        Lead(business_name="Austin Yoga Studio", city="Austin", state="TX", sources=["yellowpages"]),
        Lead(business_name="Austin Yoga Studios", city="Austin", state="TX", sources=["bing_search"]),
    ]
    d = Deduplicator(total_plugins=27)
    result = d.deduplicate(leads)
    assert len(result) == 1

def test_different_cities_not_deduplicated():
    leads = [
        Lead(business_name="Smith Dental", city="Austin", state="TX", sources=["yelp"]),
        Lead(business_name="Smith Dental", city="Dallas", state="TX", sources=["yelp"]),
    ]
    d = Deduplicator(total_plugins=27)
    result = d.deduplicate(leads)
    assert len(result) == 2

def test_confidence_score_set():
    leads = [
        Lead(business_name="Test Biz", website="https://test.com", city="NYC", state="NY", sources=["yelp"]),
        Lead(business_name="Test Biz", website="https://test.com", city="NYC", state="NY", sources=["google_maps"]),
    ]
    d = Deduplicator(total_plugins=27)
    result = d.deduplicate(leads)
    assert result[0].confidence_score == pytest.approx(2 / 27, abs=0.01)

def test_richer_fields_take_priority():
    leads = [
        Lead(business_name="Test", city="NYC", state="NY", sources=["yelp"], hook_1="Real pain point"),
        Lead(business_name="Test", city="NYC", state="NY", sources=["google"], hook_1=""),
    ]
    d = Deduplicator(total_plugins=27)
    result = d.deduplicate(leads)
    assert result[0].hook_1 == "Real pain point"
