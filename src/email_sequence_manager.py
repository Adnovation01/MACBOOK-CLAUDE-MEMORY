import sqlite3
import smtplib
import os
import time
import random
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Dict, List, Optional
from src.models.lead import Lead

SEQUENCE_DAYS = [0, 2, 6, 10, 16, 22, 29]

FRAMEWORK_TEMPLATES = {
    'aida': {
        'subject': lambda l: f"{l.city} {l.business_name.split()[0] if l.business_name else 'business'} — quick observation",
        'body': lambda l: f"""Hi,

{l.hook_1 or f"Most businesses in {l.city} in your space are losing leads to one fixable issue."}

Here's the situation: {l.email_subject_angle.replace('_', ' ') if l.email_subject_angle else 'there are gaps in your online presence your competitors are already exploiting'}.

{l.hook_2 or 'Businesses that address this typically see measurable improvement in inbound within 30 days.'}

Worth a 15-minute call this week to see if it applies to you?

Best,
{os.environ.get('YOUR_NAME', 'The Team')}""",
    },
    'bab': {
        'subject': lambda l: f"What {l.business_name.split()[0] if l.business_name else 'your business'} looks like with this solved",
        'body': lambda l: f"""Hi,

Right now, you're likely dealing with {l.pain_points[0] if l.pain_points else f'inconsistent lead flow in {l.city}'}.

Imagine instead: a predictable pipeline of inbound inquiries every week — not dependent on referrals or word of mouth.

That transformation is shorter than most business owners expect. Happy to show you how in 15 minutes.

Best,
{os.environ.get('YOUR_NAME', 'The Team')}""",
    },
    'pas': {
        'subject': lambda l: f"The {l.city} visibility gap costing you leads",
        'body': lambda l: f"""Hi,

{l.pain_points[0] if l.pain_points else f'Most businesses in {l.city} in your niche deal with inconsistent lead flow'} — and it compounds every month it goes unaddressed.

Left alone, competitors capture clients who should be calling you instead. Over 12 months, that's material revenue.

We've solved this exact problem for similar businesses. 15 minutes to show you how?

Best,
{os.environ.get('YOUR_NAME', 'The Team')}""",
    },
    'spin': {
        'subject': lambda l: f"I looked at your {l.city} presence — noticed something",
        'body': lambda l: f"""Hi,

{l.hook_1 or f"I looked at your online presence in {l.city} and noticed something worth flagging."}

{l.hook_2 or "The implication is that you're likely missing inbound inquiries that are going to competitors instead."}

If there were a straightforward way to close that gap, would that be worth 15 minutes this week?

Best,
{os.environ.get('YOUR_NAME', 'The Team')}""",
    },
    'value_wedge': {
        'subject': lambda l: "We don't count clicks — we count booked appointments",
        'body': lambda l: f"""Hi,

Most agencies measure success by traffic and impressions. We measure one thing: qualified inquiries in your pipeline.

For businesses like yours in {l.city}, that distinction matters. Traffic doesn't pay the bills.

We deliver measurable new inbound within 30 days, or we work for free until it happens.

Worth 15 minutes to see if we're a fit?

Best,
{os.environ.get('YOUR_NAME', 'The Team')}""",
    },
    '4ps': {
        'subject': lambda l: f"Specific result for {l.city} businesses — 30 days",
        'body': lambda l: f"""Hi,

Promise: consistent, predictable inbound inquiries for your business in {l.city} within 30 days.

Picture your pipeline with new leads arriving weekly — independent of referrals.

Proof: A similar business in {l.state} went from 3 inbound inquiries/month to 18 in 6 weeks using this method.

Push: I have one opening next week. Tuesday or Wednesday work for 15 minutes?

Best,
{os.environ.get('YOUR_NAME', 'The Team')}""",
    },
    'breakup': {
        'subject': lambda l: "Closing the loop — one last thing",
        'body': lambda l: f"""Hi,

This is the last email I'll send — I know timing isn't always right and I respect your inbox.

Before I go: {l.website_issues[0].replace('_', ' ') if l.website_issues else 'your Google Business listing is missing a booking link'} — worth fixing regardless of whether we work together. Takes about 5 minutes and stops you losing direct inquiries.

If things change down the road, my info is below.

Wishing you a strong quarter,
{os.environ.get('YOUR_NAME', 'The Team')}""",
    },
}

SEQUENCE = [
    ('aida',        SEQUENCE_DAYS[0]),
    ('bab',         SEQUENCE_DAYS[1]),
    ('pas',         SEQUENCE_DAYS[2]),
    ('spin',        SEQUENCE_DAYS[3]),
    ('value_wedge', SEQUENCE_DAYS[4]),
    ('4ps',         SEQUENCE_DAYS[5]),
    ('breakup',     SEQUENCE_DAYS[6]),
]

class EmailSequenceManager:
    def __init__(self, db_path: str = 'data/mission_control.db'):
        self._db = db_path
        self._setup_db()

    def _setup_db(self):
        os.makedirs(os.path.dirname(self._db) if os.path.dirname(self._db) else '.', exist_ok=True)
        with sqlite3.connect(self._db) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS email_sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_email TEXT NOT NULL,
                business_name TEXT,
                framework TEXT NOT NULL,
                scheduled_date TEXT NOT NULL,
                sent_at TEXT,
                status TEXT DEFAULT 'pending'
            )''')

    def schedule(self, lead: Lead, start_date: Optional[datetime] = None):
        if not lead.email:
            return
        start = start_date or datetime.utcnow()
        with sqlite3.connect(self._db) as conn:
            for framework, day_offset in SEQUENCE:
                send_date = start + timedelta(days=day_offset)
                conn.execute(
                    'INSERT INTO email_sequences (lead_email, business_name, framework, scheduled_date) VALUES (?,?,?,?)',
                    (lead.email, lead.business_name, framework, send_date.isoformat())
                )

    def send_due(self, lead_lookup: Dict[str, Lead]):
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self._db) as conn:
            due = conn.execute(
                "SELECT id, lead_email, framework FROM email_sequences WHERE status='pending' AND scheduled_date <= ?",
                (now,)
            ).fetchall()
        for row_id, email, framework in due:
            lead = lead_lookup.get(email)
            if not lead:
                continue
            try:
                self._send(lead, framework)
                with sqlite3.connect(self._db) as conn:
                    conn.execute(
                        "UPDATE email_sequences SET status='sent', sent_at=? WHERE id=?",
                        (datetime.utcnow().isoformat(), row_id)
                    )
                time.sleep(random.uniform(2, 5))
            except Exception as e:
                print(f"Failed {framework} to {email}: {e}")

    def mark_unsubscribed(self, email: str):
        with sqlite3.connect(self._db) as conn:
            conn.execute(
                "UPDATE email_sequences SET status='unsubscribed' WHERE lead_email=? AND status='pending'",
                (email,)
            )

    def _send(self, lead: Lead, framework: str):
        template = FRAMEWORK_TEMPLATES[framework]
        subject = template['subject'](lead)
        body = template['body'](lead)
        msg = MIMEText(body, 'plain')
        msg['Subject'] = subject
        msg['From'] = os.environ.get('EMAIL_USER', '')
        msg['To'] = lead.email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(os.environ['EMAIL_USER'], os.environ['EMAIL_PASS'])
            server.send_message(msg)
