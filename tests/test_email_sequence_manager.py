import sqlite3
from src.email_sequence_manager import EmailSequenceManager, SEQUENCE, FRAMEWORK_TEMPLATES
from src.models.lead import Lead

def make_manager(tmp_path):
    db = str(tmp_path / 'test.db')
    return EmailSequenceManager(db_path=db)

def test_schedule_creates_7_rows(tmp_path):
    mgr = make_manager(tmp_path)
    lead = Lead(business_name="Test Biz", email="test@biz.com", city="Austin", state="TX")
    mgr.schedule(lead)
    with sqlite3.connect(mgr._db) as conn:
        rows = conn.execute("SELECT * FROM email_sequences WHERE lead_email='test@biz.com'").fetchall()
    assert len(rows) == 7

def test_schedule_skips_lead_without_email(tmp_path):
    mgr = make_manager(tmp_path)
    lead = Lead(business_name="No Email Biz", email="", city="Austin", state="TX")
    mgr.schedule(lead)
    with sqlite3.connect(mgr._db) as conn:
        rows = conn.execute("SELECT * FROM email_sequences").fetchall()
    assert len(rows) == 0

def test_mark_unsubscribed_cancels_pending(tmp_path):
    mgr = make_manager(tmp_path)
    lead = Lead(business_name="Test Biz", email="unsub@biz.com", city="Austin", state="TX")
    mgr.schedule(lead)
    mgr.mark_unsubscribed("unsub@biz.com")
    with sqlite3.connect(mgr._db) as conn:
        pending = conn.execute(
            "SELECT count(*) FROM email_sequences WHERE lead_email='unsub@biz.com' AND status='pending'"
        ).fetchone()[0]
    assert pending == 0

def test_seven_frameworks_in_sequence():
    frameworks = [f for f, _ in SEQUENCE]
    assert len(frameworks) == 7
    assert 'aida' in frameworks
    assert 'breakup' in frameworks
    assert frameworks[-1] == 'breakup'

def test_aida_template_uses_hook(tmp_path):
    lead = Lead(
        business_name="Smith Dental", city="Austin", state="TX",
        hook_1="Your last review mentioned long wait times 2 weeks ago",
        hook_2="Your competitor Dr. Jones has 4.9 stars vs your 3.8"
    )
    body = FRAMEWORK_TEMPLATES['aida']['body'](lead)
    assert "long wait times" in body

def test_breakup_uses_website_issue(tmp_path):
    lead = Lead(business_name="Test", email="t@t.com", city="NYC", state="NY",
                website_issues=["no_contact_or_booking_form"])
    body = FRAMEWORK_TEMPLATES['breakup']['body'](lead)
    assert "no contact or booking form" in body

def test_sequence_cadence_is_30_days(tmp_path):
    days = [d for _, d in SEQUENCE]
    assert days[0] == 0
    assert days[-1] == 29
    assert len(days) == 7
