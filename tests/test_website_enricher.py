from src.website_enricher import WebsiteEnricher
from src.models.lead import Lead

SAMPLE_HTML = """
<html><body>
  <a href="https://facebook.com/testbiz">Facebook</a>
  <a href="https://instagram.com/testbiz_ig">Instagram</a>
  <p>Contact us: info@testbiz.com | 555-867-5309</p>
  <a href="/contact">Contact</a>
</body></html>
"""

def test_extracts_email(monkeypatch):
    enricher = WebsiteEnricher()
    monkeypatch.setattr(enricher, '_fetch', lambda url: SAMPLE_HTML)
    lead = Lead(business_name="Test Biz", website="https://testbiz.com")
    result = enricher.enrich(lead)
    assert result.email == "info@testbiz.com"

def test_extracts_phone(monkeypatch):
    enricher = WebsiteEnricher()
    monkeypatch.setattr(enricher, '_fetch', lambda url: SAMPLE_HTML)
    lead = Lead(business_name="Test Biz", website="https://testbiz.com")
    result = enricher.enrich(lead)
    assert "555" in result.phone

def test_extracts_social_links(monkeypatch):
    enricher = WebsiteEnricher()
    monkeypatch.setattr(enricher, '_fetch', lambda url: SAMPLE_HTML)
    lead = Lead(business_name="Test Biz", website="https://testbiz.com")
    result = enricher.enrich(lead)
    assert "facebook.com/testbiz" in result.facebook_url
    assert result.instagram_handle == "testbiz_ig"

def test_detects_missing_booking_form(monkeypatch):
    enricher = WebsiteEnricher()
    monkeypatch.setattr(enricher, '_fetch', lambda url: "<html><body>Hello world</body></html>")
    lead = Lead(business_name="Test Biz", website="https://testbiz.com")
    result = enricher.enrich(lead)
    assert "no_contact_or_booking_form" in result.website_issues

def test_skips_invalid_emails(monkeypatch):
    enricher = WebsiteEnricher()
    monkeypatch.setattr(enricher, '_fetch', lambda url: "<p>noreply@wix.com test@example.com real@business.com</p>")
    lead = Lead(business_name="Test Biz", website="https://testbiz.com")
    result = enricher.enrich(lead)
    assert result.email == "real@business.com"

def test_no_website_returns_lead_unchanged():
    enricher = WebsiteEnricher()
    lead = Lead(business_name="Test Biz", website="")
    result = enricher.enrich(lead)
    assert result.email == ""
    assert result.phone == ""
