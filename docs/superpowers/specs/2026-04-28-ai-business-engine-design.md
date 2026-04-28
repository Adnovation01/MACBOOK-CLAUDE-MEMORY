# AI Business Engine — Unified Control Panel
**Date:** 2026-04-28
**Status:** Approved
**Workflow:** Superpowers (brainstorm → spec → plan) + RuFlo V3 (coder/tester/reviewer swarms)

---

## 1. Problem Statement

The `ai_consulting_business` project has all the machinery — 27 scraper plugins, a 7-step email sequence engine, Gmail SMTP outreach, an Excel CRM, and LinkedIn content generation — but no unified interface. Running any function requires navigating to the right file and running Python scripts directly. Credentials are scattered across `.env` and `config/` with no UI to manage them.

**Goal:** One web-based control panel where every function is accessible, credentials are manageable, and the whole pipeline runs from a single screen.

---

## 2. Decisions Made

| Decision | Choice | Reason |
|---|---|---|
| App type | Web app (browser) | Extends existing Flask backend; no extra tooling |
| Visual style | Clean Light | White, minimal, scannable — Notion/Stripe aesthetic |
| Navigation | Left sidebar | Always-visible section list; standard for SaaS dashboards |
| Frontend tech | HTMX + Jinja2 | No npm, no build step, all Python, real-time via polling |
| Credential storage | `.env` file | Simple, local-only, never committed to git |
| JS dependency | `htmx.min.js` (~14kb) | Single file, no framework |

---

## 3. Architecture

### Stack
- **Backend:** Flask (existing `app.py`, extended)
- **Templates:** Jinja2 (`templates/` directory, new)
- **Frontend:** HTMX for dynamic updates + plain CSS (Clean Light theme)
- **Database:** SQLite `data/mission_control.db` (existing)
- **Credentials:** `.env` file, read via `python-dotenv`

### File Structure
```
ai_consulting_business/
├── app.py                          ← extend with new routes
├── templates/
│   ├── base.html                   ← sidebar shell (shared layout)
│   ├── dashboard.html
│   ├── scraper.html
│   ├── leads.html
│   ├── outreach.html
│   ├── content.html
│   ├── plugins.html
│   └── settings.html
├── static/
│   ├── style.css                   ← Clean Light theme
│   └── htmx.min.js                 ← single JS dependency
├── src/                            ← all existing Python, unchanged
└── config/
    └── scraper_config.json         ← plugin toggles (existing)
```

### Shared Layout (`base.html`)
Every page extends `base.html` which renders:
- Left sidebar (220px, fixed) with logo, nav sections, nav items, logged-in user
- Topbar (56px, white) with page title + contextual action buttons
- Main content area (scrollable)

---

## 4. Sections

### 4.1 Dashboard (`/`)
**Purpose:** At-a-glance campaign health.

**Content:**
- 4 stat cards: Total Leads, Emails Sent, Replies, Queue (due today)
- Recent Leads table (last 10): business name, location, email, intent score, status badge
- Action buttons: Export Excel, New Campaign (→ Scraper)

**Data sources:** `GET /api/leads` (existing), `GET /api/scrape/status` (new)

---

### 4.2 Scraper (`/scraper`)
**Purpose:** Launch a scraping campaign and watch it run live.

**Content:**
- Form: Industry/niche (text), Location (text), Max Leads (select: 50/100/200/500)
- ▶ Run Campaign button → `POST /api/scrape`
- Live progress card (HTMX polls `/api/scrape/status` every 2s):
  - Progress bar (0–100%)
  - Lead count as they arrive
  - Current plugin name
  - Done state with total found

**State management:** A module-level `scrape_state` dict in `app.py` tracks `{running, progress, leads_found, current_plugin, error}`. Background thread updates it; status endpoint reads it.

---

### 4.3 Leads CRM (`/leads`)
**Purpose:** View, filter, and act on all scraped leads.

**Content:**
- Search input (client-side filter)
- Filter dropdowns: State, Niche, Status
- Table: Business, Email, Location, Niche, Intent Score, Pain Points, Action dropdown
- Action dropdown per row: READY / SEND / SKIP / DONE → `POST /api/update-lead` (existing)
- Export Excel button → `GET /api/leads/export` (new, returns `.xlsx`)

---

### 4.4 Outreach (`/outreach`)
**Purpose:** Manage the 7-step email sequence queue.

**Content:**
- Tabs: Queue / Sent / Failed
- Queue tab: table of pending emails — business, email, framework badge (AIDA/BAB/PAS…), sequence day, scheduled date, Preview button
- Preview modal: renders the full email subject + body before sending
- ▶ Send Due Emails (N) button → `POST /api/outreach/send-due`
- HTMX refreshes table after send
- Unsubscribe link per lead row

**Data source:** `email_sequences` table in `mission_control.db` (existing)

---

### 4.5 Content (`/content`)
**Purpose:** Generate LinkedIn posts from recent lead research.

**Content:**
- ✨ Generate Posts button → `POST /api/content/generate`
- Generated post cards: title, body text, 📋 Copy to clipboard button
- Posts persisted to `data/marketing_content.json` (existing)

---

### 4.6 Plugins (`/plugins`)
**Purpose:** Enable/disable all 27 scraper plugins; manage social credentials.

**Content:**
- 4 groups: Search Engines / Directories / Social (requires credentials) / Reviews & Niche
- Each plugin: name label + toggle switch
- Toggle → `POST /api/plugins/toggle` → updates `config/scraper_config.json`
- Social plugins (LinkedIn, Facebook, Instagram, Twitter) show credential input fields when enabled
- Save Changes button

---

### 4.7 Settings (`/settings`)
**Purpose:** Manage all credentials and identity in one form.

**Content (4 cards):**

**Gmail Outreach:**
- Gmail address (`EMAIL_USER`)
- App password (`EMAIL_PASS`) — password input
- BCC email (`BCC_EMAIL`)
- ✅ Test Connection button → `POST /api/settings/test-gmail` → SMTP login check

**API Keys:**
- OpenAI API key (`OPENAI_API_KEY`)
- Resend API key (`RESEND_API_KEY`)

**Your Identity:** (also used as email sender name)
- Name (`YOUR_NAME`), Title (`YOUR_TITLE`), Website (`YOUR_WEBSITE`)

**Campaign Defaults:**
- Default niche (`DEFAULT_NICHE`), Default location (`DEFAULT_LOCATION`)

**Save:** `POST /api/settings/save` → reads current `.env`, merges, writes back. Flash message on success.

**Note:** Credential fields show masked values if already set (e.g. `••••••••`). Never echoed in plaintext.

---

## 5. New API Routes Required

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Dashboard page |
| GET | `/scraper` | Scraper page |
| GET | `/leads` | Leads CRM page |
| GET | `/outreach` | Outreach page |
| GET | `/content` | Content page |
| GET | `/plugins` | Plugins page |
| GET | `/settings` | Settings page |
| GET | `/api/scrape/status` | Live scraping progress (HTMX poll) |
| GET | `/api/leads/export` | Download leads as `.xlsx` |
| GET | `/api/outreach/queue` | Pending email sequences |
| POST | `/api/outreach/send-due` | Fire due emails now |
| POST | `/api/content/generate` | Generate LinkedIn posts |
| POST | `/api/plugins/toggle` | Toggle plugin on/off |
| POST | `/api/settings/save` | Write credentials to `.env` |
| POST | `/api/settings/test-gmail` | Test Gmail SMTP login |

Existing routes (`/api/login`, `/api/logout`, `/api/leads`, `/api/scrape`, `/api/update-lead`) remain unchanged.

---

## 6. Data Flow

### Scraping
```
Scraper form → POST /api/scrape → background thread
→ scrape_state updated every plugin completion
→ HTMX polls /api/scrape/status every 2s → progress bar
→ Leads saved to SQLite + leads.json
→ EmailSequenceManager.schedule() called per lead
```

### Outreach
```
Leads CRM → mark SEND → POST /api/update-lead
→ Outreach queue shows pending sequences
→ "Send Due" button → POST /api/outreach/send-due
→ EmailSequenceManager.send_due() → Gmail SMTP
→ HTMX refreshes queue table
```

### Credentials
```
Settings form → POST /api/settings/save
→ Read .env lines → merge new values → write back
→ dotenv reload → flash "Saved ✓"
→ "Test Gmail" → SMTP login attempt → ok/fail banner
```

---

## 7. Error Handling

- **Scraper plugin failures:** Silent (existing behavior) — log warning, skip plugin, continue
- **Gmail SMTP errors:** Red banner on Outreach page with exact error message
- **Settings test failure:** Inline error message under the Gmail card
- **Missing credentials:** Outreach page shows warning banner if `EMAIL_USER`/`EMAIL_PASS` not set
- **Background thread crash:** Caught, stored in `scrape_state['error']`, shown on Scraper page

---

## 8. Out of Scope

- Multi-user collaboration (existing `team.json` auth stays as-is)
- Deployment to a remote server
- Mobile responsiveness (internal tool, desktop browser only)
- Real-time WebSocket streaming (HTMX polling every 2s is sufficient)
