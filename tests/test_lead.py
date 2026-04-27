from src.models.lead import Lead

def test_lead_defaults():
    lead = Lead(business_name="Test Biz", city="Austin", state="TX")
    assert lead.email == ""
    assert lead.intent_score == 0
    assert lead.sources == []
    assert lead.confidence_score == 0.0

def test_lead_to_dict():
    lead = Lead(business_name="Test Biz", city="Austin", state="TX", sources=["yelp"])
    d = lead.to_dict()
    assert d["business_name"] == "Test Biz"
    assert d["sources"] == ["yelp"]
    assert "scraped_at" in d

def test_lead_accepts_pain_points():
    lead = Lead(business_name="Test", pain_points=["slow service", "bad reviews"])
    assert len(lead.pain_points) == 2

def test_lead_website_issues_default_empty():
    lead = Lead()
    assert lead.website_issues == []
