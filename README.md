# AI Consulting Business — Universal Lead Scraper

Keyword-driven B2B lead generation engine. Give it a niche and location, it scrapes 27 sources in parallel, extracts real contact info and pain points, then fires a 7-email outreach sequence per lead over 30 days.

---

## Quick Start

### 1. Install dependencies

```bash
pip3 install flask flask-login flask-cors requests beautifulsoup4 pandas openpyxl python-dotenv
pip3 install playwright && playwright install chromium
pip3 install praw  # optional — only needed for Reddit enrichment
```

### 2. Set environment variables

Create a `.env` file in the project root (never commit this):

```env
EMAIL_USER=your-gmail@gmail.com
EMAIL_PASS=your-gmail-app-password
YOUR_NAME=Your Name

# Optional — only if you want Reddit pain-point enrichment
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
```

> **Gmail setup:** Use an App Password (myaccount.google.com/apppasswords), not your main password. Enable 2FA first.

### 3. Run the Flask server

```bash
python3 app.py
```

Server starts at http://localhost:5000.

### 4. Start a scraping campaign

```bash
curl -X POST http://localhost:5000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"keyword": "dentist", "location": "Austin, TX", "max_leads": 100}'
```

Or change the keyword for any niche:

```bash
# Roofing contractors in Dallas
curl -X POST http://localhost:5000/api/scrape \
  -d '{"keyword": "roofing contractor", "location": "Dallas, TX", "max_leads": 50}'

# Yoga studios in Miami
curl -X POST http://localhost:5000/api/scrape \
  -d '{"keyword": "yoga studio", "location": "Miami, FL", "max_leads": 75}'
```

Scraping runs in the background. Results are saved to `data/leads.json` and the 7-email sequence is automatically scheduled for each lead with an email address.

---

## How It Works

```
keyword + location
      |
      v
27 plugins fire in parallel
      |
      v
Deduplication (same business from multiple sources -> 1 merged lead)
      |
      v
Website Enricher (visit each URL -> extract email, phone, social links)
      |
      v
Intent Scoring (ranks leads by conversion likelihood)
      |
      v
7-email sequence scheduled per lead (fires over 30 days)
```

---

## Data Sources (27 Plugins)

| Tier | Sources |
|---|---|
| Search engines | DuckDuckGo, Bing, Google Search |
| Business directories | YellowPages, Google Maps, Yelp, BBB, Manta, Superpages, Hotfrog, Whitepages, Foursquare, Cylex, Clutch, Brownbook |
| Social media | Facebook, Instagram, LinkedIn, Twitter/X, YouTube |
| Community | Reddit (pain-point enrichment) |
| Review platforms | Trustpilot, Healthgrades, Angi, Thumbtack |
| Public records | OpenCorporates, State Business Registries |

Social media sources (Facebook, Instagram, LinkedIn, Twitter) require login cookies — see Authenticated Sources below.

---

## Email Sequence (7 Emails Over 30 Days)

First 2 emails are plain text only for maximum deliverability.

| Email | Day | Framework | Purpose |
|---|---|---|---|
| 1 | Day 1 | AIDA | Opens with a specific observation from scraped data |
| 2 | Day 3 | BAB (Before/After/Bridge) | Transformation from pain to solution |
| 3 | Day 7 | PAS (Problem/Agitate/Solution) | Names their exact problem and consequences |
| 4 | Day 11 | SPIN | References specific detail found (reviews, rating, competitor gap) |
| 5 | Day 17 | Value Wedge | Differentiates you from other agencies |
| 6 | Day 23 | 4Ps (Promise/Picture/Proof/Push) | Case study with real numbers, hard ask |
| 7 | Day 30 | Breakup Email | Final touch, free insight, no pressure |

### Send due emails (run daily)

```bash
python3 -c "
from src.email_sequence_manager import EmailSequenceManager
from src.models.lead import Lead
from dataclasses import fields as dc_fields
import json

with open('data/leads.json') as f:
    leads_data = json.load(f)

lead_lookup = {}
for d in leads_data:
    lead = Lead(**{k: d.get(k, '') for k in [f.name for f in dc_fields(Lead)] if k in d})
    if lead.email:
        lead_lookup[lead.email] = lead

mgr = EmailSequenceManager()
mgr.send_due(lead_lookup)
"
```

### Handle unsubscribes

```python
from src.email_sequence_manager import EmailSequenceManager
mgr = EmailSequenceManager()
mgr.mark_unsubscribed("someone@business.com")
```

---

## Authenticated Sources

Export cookies from your logged-in browser and save them as JSON files:

```
config/sessions/
  facebook.json
  instagram.json
  linkedin.json
  twitter.json
```

Use the EditThisCookie Chrome extension: log in to the platform, click the extension, Export, paste the JSON into the file. The scraper loads these on startup. If a session expires, that plugin is skipped and the rest continue.

---

## Enable/Disable Sources

Edit `config/scraper_config.json`:

```json
{
  "plugins": {
    "facebook": {"enabled": false},
    "healthgrades": {"enabled": true}
  }
}
```

Niche-specific plugins activate automatically based on your keyword:

| Keyword | Extra plugins activated |
|---|---|
| dentist, doctor | Healthgrades |
| roofing, plumbing | Angi, Thumbtack |
| yoga, fitness | Thumbtack |

---

## Lead Data Captured

- Contact: name, email, phone, address, city, state, website
- Social profiles: Facebook, Instagram, LinkedIn, Twitter, YouTube
- Review signals: rating, review count, platform, recent negative reviews
- Pain points: from real reviews and Reddit (not synthetic/hardcoded)
- hook_1, hook_2: specific things to reference in outreach emails
- Intent score 0-100: based on negative reviews, no contact form, no social, competitor gaps
- Ad signals: whether they run Google or Facebook ads

Saved to: `data/leads.json`, `data/mission_control.db`, and `Dentist_Industry_Master.xlsx`

---

## Dashboard

```bash
python3 app.py
# Open http://localhost:5000/mission-hub
```

Login with credentials from `config/team.json`.

---

## Reddit Setup (Optional)

1. Go to reddit.com/prefs/apps
2. Create a "script" app
3. Add to `.env`:

```env
REDDIT_CLIENT_ID=abc123
REDDIT_CLIENT_SECRET=xyz789
```

---

## Run Tests

```bash
python3 -m pytest tests/ -v
# 66 passed
```

---

## Project Structure

```
src/
  models/lead.py              # Lead data schema (33 fields)
  plugins/                    # All 27 scraper plugins
  scraper_orchestrator.py     # Parallel fan-out engine
  deduplicator.py             # Merge duplicate leads across sources
  website_enricher.py         # Email/phone/social extraction
  session_manager.py          # Cookie auth for social plugins
  rate_limiter.py             # Per-source delays and backoff
  email_sequence_manager.py   # 7-email drip scheduler
  plugins/plugin_factory.py   # Builds all 27 plugins from config

config/
  scraper_config.json         # Enable/disable plugins per source
  sessions/                   # Browser cookies (gitignored)

data/
  leads.json                  # Scraped leads output
  mission_control.db          # SQLite database

tests/                        # 66 tests, all passing
docs/superpowers/
  specs/                      # Design documents
  plans/                      # Implementation plans
```
