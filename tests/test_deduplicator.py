import os
import sqlite3
import tempfile
import pytest
from src.deduplicator import Deduplicator
from src.models.lead import Lead


def _make_db_with_leads(leads_data):
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    with sqlite3.connect(tmp.name) as conn:
        conn.execute('CREATE TABLE leads (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, phone TEXT)')
        for email, phone in leads_data:
            conn.execute('INSERT INTO leads (email, phone) VALUES (?, ?)', (email, phone))
    return tmp.name

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


def test_filter_existing_removes_duplicate_email():
    db_path = _make_db_with_leads([('existing@dental.com', ''), ('', '555-0001')])
    leads = [
        Lead(business_name="Old Practice", email="existing@dental.com", phone="", sources=["yelp"]),
        Lead(business_name="New Practice", email="new@dental.com", phone="", sources=["yelp"]),
    ]
    d = Deduplicator()
    new_leads, skipped = d.filter_existing(leads, db_path)
    os.unlink(db_path)
    assert len(new_leads) == 1
    assert new_leads[0].business_name == "New Practice"
    assert skipped == 1


def test_filter_existing_removes_duplicate_phone():
    db_path = _make_db_with_leads([('', '555-9999')])
    leads = [
        Lead(business_name="Dup Phone Biz", email="different@email.com", phone="555-9999", sources=["bbb"]),
        Lead(business_name="Unique Biz", email="unique@email.com", phone="555-0002", sources=["bbb"]),
    ]
    d = Deduplicator()
    new_leads, skipped = d.filter_existing(leads, db_path)
    os.unlink(db_path)
    assert len(new_leads) == 1
    assert new_leads[0].business_name == "Unique Biz"
    assert skipped == 1


def test_filter_existing_keeps_all_when_db_empty():
    db_path = _make_db_with_leads([])
    leads = [
        Lead(business_name="Brand New A", email="a@new.com", sources=["yelp"]),
        Lead(business_name="Brand New B", email="b@new.com", sources=["yelp"]),
    ]
    d = Deduplicator()
    new_leads, skipped = d.filter_existing(leads, db_path)
    os.unlink(db_path)
    assert len(new_leads) == 2
    assert skipped == 0


def test_filter_existing_email_comparison_is_case_insensitive():
    db_path = _make_db_with_leads([('Info@DentalCare.Com', '')])
    leads = [
        Lead(business_name="Same Biz", email="info@dentalcare.com", sources=["yelp"]),
    ]
    d = Deduplicator()
    new_leads, skipped = d.filter_existing(leads, db_path)
    os.unlink(db_path)
    assert len(new_leads) == 0
    assert skipped == 1


def test_filter_existing_returns_all_on_db_error():
    leads = [Lead(business_name="Any Biz", email="x@y.com", sources=["yelp"])]
    d = Deduplicator()
    new_leads, skipped = d.filter_existing(leads, "/nonexistent/path/db.sqlite")
    assert len(new_leads) == 1
    assert skipped == 0
