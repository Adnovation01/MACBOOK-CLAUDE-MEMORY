# Universal Multi-Source Lead Scraper — Design Spec
**Date:** 2026-04-27
**Status:** Approved

---

## 1. Goal

Upgrade `ai_consulting_business` from a YellowPages-only scraper to a universal lead generation engine that:
- Accepts any business niche keyword at runtime
- Scrapes 27 sources in parallel (search engines, directories, social media, review platforms, public records)
- Extracts maximum data per lead (name, email, phone, address, all social profiles, real pain points, conversion signals)
- Fires a 7-email drip sequence per lead over 30 days using a different copywriting framework per email
- Operates 100% free (no paid APIs), with user-provided session cookies for authenticated sources

---

## 2. Architecture: Modular Plugin Orchestrator

### 2.1 Orchestrator (`src/scraper_orchestrator.py`)

Central engine. Accepts:
- `keyword` — business niche (e.g. "dentist", "roofing contractor", "yoga studio")
- `location` — city/state or "nationwide"
- `max_leads` — target lead count

Fans out to all enabled plugins simultaneously via `concurrent.futures.ThreadPoolExecutor`. Collects raw leads, passes to deduplication engine, then website enricher, then feeds existing pipeline unchanged.

### 2.2 Plugin Base Interface (`src/plugins/base_plugin.py`)

```python
class BasePlugin:
    name: str                    # e.g. "facebook", "yelp"
    requires_auth: bool          # True for FB/IG/LinkedIn/Twitter
    rate_limit_seconds: float    # min delay between requests

    def search(self, keyword: str, location: str, max_leads: int) -> List[Lead]
    def is_available(self) -> bool  # checks session valid + site reachable
```

Every plugin is independent. A failed/blocked plugin does not stop others.

---

## 3. Source Coverage: 27 Plugins

### Tier 1 — Search Engines (broadest discovery)
- `google_search_plugin.py` — Google Search results, keyword + location queries
- `bing_search_plugin.py` — Bing Search (less aggressive blocking than Google)
- `duckduckgo_plugin.py` — DuckDuckGo (no CAPTCHA, most lenient)

### Tier 2 — Business Directories
- `yellowpages_plugin.py` — existing scraper, refactored to plugin interface
- `google_maps_plugin.py` — Playwright, extracts name/address/phone/website/reviews
- `yelp_plugin.py` — listings + review data
- `bbb_plugin.py` — Better Business Bureau
- `manta_plugin.py` — Manta.com directory
- `superpages_plugin.py` — Superpages.com
- `hotfrog_plugin.py` — Hotfrog.com
- `whitepages_plugin.py` — Whitepages business listings
- `foursquare_plugin.py` — Foursquare public data
- `cylex_plugin.py` — Cylex directory
- `clutch_plugin.py` — Clutch.co (B2B focus)
- `brownbook_plugin.py` — Brownbook.net

### Tier 3 — Social Media (authenticated via session cookies)
- `facebook_plugin.py` — Facebook Business pages, posts, reviews, ad signals
- `instagram_plugin.py` — Instagram Business profiles, follower count, post sentiment
- `linkedin_plugin.py` — LinkedIn company search, employee count, industry signals
- `twitter_plugin.py` — Twitter/X business accounts, complaint mentions
- `youtube_plugin.py` — YouTube business channels

### Tier 4 — Community / Reddit
- `reddit_plugin.py` — PRAW free API; searches subreddits for keyword mentions, extracts real complaints and pain points about businesses in the niche

### Tier 5 — Review Platforms (keyword-adaptive)
Plugin activation is controlled by `config/scraper_config.json` niche mappings — e.g. keyword "dentist" activates `healthgrades` and `zocdoc`; keyword "roofer" activates `angi` and `thumbtack`. Default: `trustpilot` + `thumbtack` always active for any keyword.
- `trustpilot_plugin.py` — general reviews (always active)
- `healthgrades_plugin.py` — medical/dental niches
- `angi_plugin.py` — home services (roofing, plumbing, etc.)
- `thumbtack_plugin.py` — local service providers (always active)

### Tier 6 — Public / Government Data
- `opencorporates_plugin.py` — registered company data, officers, registered address
- `state_registry_plugin.py` — Secretary of State websites (50 states, legally public)

### Tier 7 — Website Enricher (`src/website_enricher.py`)
Visits every URL discovered by any plugin:
- Extracts email via regex
- Extracts phone via regex
- Discovers social profile links (Facebook, Instagram, LinkedIn, Twitter, YouTube)
- Detects missing contact form, missing SSL, slow-load signals
- Extracts pain-point text from "Reviews" or "Testimonials" sections

---

## 4. Lead Schema

```python
@dataclass
class Lead:
    # Identity
    business_name: str
    website: str
    email: str
    phone: str
    address: str
    city: str
    state: str

    # Social profiles
    facebook_url: str
    instagram_handle: str
    linkedin_url: str
    twitter_handle: str
    youtube_channel: str

    # Signals (real scraped data)
    review_count: int
    avg_rating: float
    review_platform: str           # "google", "yelp", etc.
    reddit_mentions: List[str]     # actual post excerpts
    runs_google_ads: bool
    runs_fb_ads: bool
    pain_points: List[str]         # from real reviews/posts, NOT synthetic

    # Conversion intelligence
    intent_score: int              # 0–100 composite
    recent_negative_reviews: List[str]   # last 90 days with text
    unanswered_reviews: int        # owner never responded
    website_issues: List[str]      # no SSL, no booking form, broken links
    no_social_presence: bool
    competitor_advantage: str      # what nearby competitor does better
    last_ad_seen: date
    hook_1: str                    # e.g. "Your last review mentioned 'long waits' 3 weeks ago"
    hook_2: str                    # e.g. "Top competitor has 4.9★ vs your 3.8★"
    best_contact_time: str
    email_subject_angle: str       # "negative_reviews" | "competitor_gap" | "missing_leads" | "dead_website"

    # Metadata
    sources: List[str]             # ["google_maps", "yelp", "facebook"]
    confidence_score: float        # len(sources) / total_plugins
    scraped_at: datetime
```

### Intent Score Calculation

| Signal | Points |
|---|---|
| 1+ negative review in last 30 days | +25 |
| Owner never replies to reviews | +20 |
| No booking/contact form on website | +15 |
| Competitors in same city have higher rating | +15 |
| Ran Google/FB ads but stopped | +15 |
| No Instagram or Facebook presence | +10 |

---

## 5. Deduplication Engine (`src/deduplicator.py`)

- Primary match key: `business_name` + `city` (fuzzy, 85% similarity threshold)
- Secondary: `website` exact match (strongest signal)
- Merge rule: keep richest field per attribute across all sources
- `sources` list accumulates all plugins that confirmed the lead
- `confidence_score = len(sources) / total_active_plugins`

---

## 6. Session Manager (`src/session_manager.py`)

Authenticated sources (Facebook, Instagram, LinkedIn, Twitter) use user-provided browser cookies.

```
config/sessions/
  facebook.json
  instagram.json
  linkedin.json
  twitter.json
```

- Loads cookies at startup, injects into Playwright browser context
- Detects expired session (login redirect detected) → logs warning, skips plugin, others continue
- User refreshes by exporting cookies from browser and replacing the JSON file

---

## 7. Rate Limiter (`src/rate_limiter.py`)

| Source | Delay Range | Block Response |
|---|---|---|
| Google Maps/Search | 8–15s random | Exponential backoff, skip after 3 fails |
| Facebook/Instagram | 5–10s random | Rotate User-Agent, 30s cooldown |
| Reddit (PRAW API) | 2s fixed | Respect 429 header |
| YellowPages/Yelp | 3–6s random | Skip page, continue |
| All directories | 2–4s random | Skip, log |

All delays are randomized within range. Fixed intervals are detectable as bots.

User-Agent rotation pool of 12 realistic browser strings, rotated per request per plugin.

---

## 8. 7-Email Sequence Engine (`src/email_sequence_manager.py`)

One sequence per lead, fires over 30 days. Each email uses a different copywriting framework.

### Why plain text for emails 1 & 2
HTML formatting signals marketing to spam filters (scores higher for commercial intent) and to the recipient's brain (triggers "marketing email" classification in <300ms). Plain text achieves ~25% higher open rates in cold outbound. Emails 1–2 are plain text only to protect domain reputation and maximize deliverability.

### The Sequence

| # | Day | Framework | Subject Line Pattern | Format | Primary Mechanism |
|---|---|---|---|---|---|
| 1 | 1 | **AIDA** + hyper-personalized observation | Industry + local + pattern interrupt | Plain text | Attention-to-action funnel; uses `hook_1` from real data |
| 2 | 3 | **BAB** (Before/After/Bridge) | Future-state framing | Plain text | Emotional transformation; "Right now you're probably..." |
| 3 | 7 | **PAS** (Problem/Agitate/Solution) | Loss aversion: names exact pain | Plain text | Pain recognition from new angle |
| 4 | 11 | **SPIN** (Situation/Problem/Implication/Need-Payoff) | Research signal: "I looked at your reviews" | Plain text | Uses `hook_1` + `hook_2`; highest-converting email in sequence |
| 5 | 17 | **Value Wedge** | Differentiation framing | Plain text + 1 bolded line | Answers "why you" objection explicitly |
| 6 | 23 | **4Ps** (Promise/Picture/Proof/Push) | Proof-forward: number + outcome + timeframe | Plain text + case study callout | Hard proof, specific case study, hard ask |
| 7 | 30 | **Breakup Email** + Curiosity Gap | Closure: "Closing the loop — one last thing" | Plain text | Loss aversion, final value gift, no-pressure close |

### Subject Line Rules (SMB psychology)
- Under 40 characters (mobile preview truncates at ~40)
- Front-load critical information
- No newsletter signals ("special offer", "free", "% off")
- Use local specificity (+15–22% open rate lift)
- Loss-aversion framing outperforms gain framing by 20–30% for SMB owners
- Specific numbers ("47 reviews", "22 booked jobs") > round numbers

### Sequence Controls
- Unsubscribe detection: reply contains stop/unsubscribe/remove → sequence halts immediately
- Gmail SMTP with 2–5s jitter between sends
- Per-lead sequence state stored in SQLite (`mission_control.db`)
- Email 7 always includes one real, useful free insight about the lead's business

---

## 9. Data Flow (End to End)

```
User inputs: keyword + location + max_leads
        ↓
Orchestrator fans out to all 27 plugins (parallel)
        ↓
Raw leads per source → Deduplication Engine
        ↓
Merged leads → Website Enricher (fills missing email/phone/social)
        ↓
Conversion Intelligence layer (intent_score, hook_1, hook_2, email_subject_angle)
        ↓
data/leads.json + SQLite (mission_control.db)
        ↓
Email Sequence Manager — schedules 7-email sequence per lead
        ↓
Gmail SMTP sender — fires on cadence (Day 1, 3, 7, 11, 17, 23, 30)
        ↓
Excel Manager — updates Dentist_Industry_Master.xlsx
        ↓
dashboard/crm_data.json — updates web UI
```

---

## 10. File Organization

```
src/
  scraper_orchestrator.py        # central fan-out engine
  deduplicator.py                # merge same business from multiple sources
  website_enricher.py            # visit URLs, extract contact + social data
  session_manager.py             # cookie-based auth for social plugins
  rate_limiter.py                # per-source delays + backoff
  email_sequence_manager.py      # 7-email scheduler + framework templates
  plugins/
    base_plugin.py               # abstract base class
    google_search_plugin.py
    bing_search_plugin.py
    duckduckgo_plugin.py
    google_maps_plugin.py
    yellowpages_plugin.py        # refactored from genuine_campaign.py
    yelp_plugin.py
    bbb_plugin.py
    manta_plugin.py
    superpages_plugin.py
    hotfrog_plugin.py
    whitepages_plugin.py
    foursquare_plugin.py
    cylex_plugin.py
    clutch_plugin.py
    brownbook_plugin.py
    facebook_plugin.py
    instagram_plugin.py
    linkedin_plugin.py
    twitter_plugin.py
    youtube_plugin.py
    reddit_plugin.py
    trustpilot_plugin.py
    healthgrades_plugin.py
    angi_plugin.py
    thumbtack_plugin.py
    opencorporates_plugin.py
    state_registry_plugin.py

config/
  scraper_config.json            # enable/disable plugins, rate limits
  sessions/
    facebook.json
    instagram.json
    linkedin.json
    twitter.json

docs/
  superpowers/specs/
    2026-04-27-universal-scraper-design.md   # this file
```

---

## 11. What Does NOT Change

The following existing modules are kept exactly as-is and receive output from the new pipeline:
- `email_generator.py` — now uses real `pain_points` + `hook_1`/`hook_2` instead of synthetic pools
- `excel_manager.py` — unchanged
- `database_manager.py` — unchanged (Lead schema extends existing fields)
- `outreach_manager.py` — enhanced with sequence scheduling
- `app.py` Flask server — new `/api/scrape` accepts `keyword` + `location` params
- `dashboard/` — unchanged

---

## 12. Out of Scope

- Paid APIs (Google Places API, Apollo.io, Hunter.io, etc.)
- Proxy rotation services (no budget)
- CAPTCHA solving services
- Any AI/LLM for email generation (existing template system retained)
