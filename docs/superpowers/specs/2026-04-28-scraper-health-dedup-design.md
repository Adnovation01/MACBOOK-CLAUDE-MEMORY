# Scraper: Plugin Health Monitoring, Deduplication & Anti-Hallucination Design
**Date:** 2026-04-28
**Status:** Approved

---

## Problem Statement

The scraper app has four critical gaps:
1. Plugin failures are silently swallowed — no way to know which plugins are down
2. `Deduplicator` only deduplicates within a single run — cross-campaign duplicates accumulate in the DB
3. `real_stealth_scraper.py` fabricates pain points and market gap data using random pools
4. No pre-flight gate — scrapes start without verifying plugin availability

---

## Decisions

| Question | Decision |
|---|---|
| Health visibility | Both: plugin cards show status badges AND scraper page shows pre-flight panel |
| Deduplication key | Email OR phone — same contact = duplicate regardless of business name |
| Diagnostic check type | Hybrid: lightweight (HTTP HEAD, cached 5min) before every scrape + on-demand full probe |
| `real_stealth_scraper.py` | Delete — superseded by plugin system, source of hallucination |
| `degraded` plugins | Skip — do not attempt, report in summary |
| Run button gate | Informational only — always enabled, pre-flight is advisory |

---

## Architecture

### New File
**`src/plugin_health_monitor.py`** — single owner of all plugin health state.

### Modified Files
- `src/plugins/base_plugin.py` — add `health_check() -> dict` (default: returns healthy; each plugin overrides with HTTP HEAD to its target domain)
- `src/scraper_orchestrator.py` — consult `PluginHealthMonitor` before running; skip non-healthy plugins; extend `scrape_state` with skipped plugin list
- `src/deduplicator.py` — add DB-aware deduplication mode (email/phone cross-reference)
- `app.py` — add `GET /api/plugins/health` and `POST /api/plugins/diagnose` endpoints; extend scrape result with `duplicates_skipped` and `plugins_skipped`
- `templates/plugins.html` — async status badges per plugin card + "Run Full Diagnostics" button
- `templates/scraper.html` — pre-flight panel showing healthy/degraded/failed counts before run

### Deleted Files
- `src/real_stealth_scraper.py`

### Data Flow
```
[User opens Scraper page]
  → GET /api/plugins/health (lightweight, cached 5min)
  → pre-flight panel renders with counts + failed plugin names

[User clicks Run]
  → ScraperOrchestrator.scrape()
  → PluginHealthMonitor.get_healthy_plugins() → only healthy ones run
  → each plugin result logged back to health monitor
  → Deduplicator.filter_existing() → cross-references leads table (email/phone)
  → contact validation gate → drop leads without any contact vector
  → net-new leads saved to DB
  → scrape_state updated: leads_found, duplicates_skipped, plugins_run, plugins_skipped

[User opens Plugins page]
  → async fetch of /api/plugins/health → status badges render
  → [Run Full Diagnostics] → POST /api/plugins/diagnose → full probe → badges refresh
```

---

## Component Details

### PluginHealthMonitor (`src/plugin_health_monitor.py`)

**Health states:** `healthy` | `degraded` | `failed` | `unknown`

**Lightweight check:**
- Calls `plugin.health_check()` per plugin
- Default: HTTP HEAD to plugin's target domain, 5s timeout
- Auth-required plugins with missing credentials → `degraded`
- Result cached in memory dict `{plugin_name: {status, checked_at, error}}`
- Cache TTL: 5 minutes
- Persisted to `data/plugin_health.json` on each update (survives restarts)

**Full probe:**
- Calls `plugin.search("dentist", "New York", 1)`, expects ≥ 1 result
- 30s timeout per plugin, all run in parallel
- Writes results to same cache + `data/plugin_health.json`

**API response shape (`GET /api/plugins/health`):**
```json
{
  "summary": {"healthy": 22, "degraded": 3, "failed": 2},
  "plugins": {
    "duckduckgo": {"status": "healthy", "checked_at": "2026-04-28T10:00:00Z", "error": null},
    "facebook":   {"status": "degraded", "checked_at": "...", "error": "missing credentials"},
    "yelp":       {"status": "failed",   "checked_at": "...", "error": "HTTP 403 Forbidden"}
  }
}
```

### BasePlugin changes (`src/plugins/base_plugin.py`)

```python
def health_check(self) -> dict:
    # Override in subclasses that have a specific target URL
    # Default: return healthy (subclasses override with HTTP HEAD)
    return {"status": "healthy", "error": None}
```

Each plugin that scrapes a known domain overrides `health_check()` to do an HTTP HEAD to that domain.

### Deduplicator changes (`src/deduplicator.py`)

New method `filter_existing(leads, db_path)`:
- Accepts a list of leads and the SQLite DB path
- Queries `SELECT email, phone FROM leads` once (single read)
- Builds sets of known emails and phones
- Returns `(new_leads, skipped_count)` — filters out any lead whose email or phone already exists

The existing in-session `deduplicate()` method is unchanged and still runs first (merges leads from different plugins within the same run). The DB check runs after, at insert time.

### Anti-Hallucination Enforcement

- `real_stealth_scraper.py` deleted
- No random pools, no `random.sample`, no `random.choice` for data fields anywhere in the codebase
- `pain_points`, `hook_1`, `hook_2`, `competitor_advantage`, `website_issues` must be populated only by `WebsiteEnricher` from actual scraped content
- Fields left as `""` / `[]` if not found — never synthesized

### Scrape State (extended)

```python
scrape_state = {
    'running': False,
    'progress': 0,
    'leads_found': 0,
    'duplicates_skipped': 0,       # NEW
    'plugins_run': 0,              # NEW
    'plugins_skipped': [],         # NEW — list of names
    'current_plugin': '',
    'error': None
}
```

### UI: Plugins Page

- On page load: `fetch('/api/plugins/health')` → renders a status dot on each plugin card
  - Green = `healthy`, Yellow = `degraded`, Grey = `unknown`, Red = `failed`
- "Run Full Diagnostics" button at top → `POST /api/plugins/diagnose` → polling until done → badges refresh
- Tooltip on hover shows error message for failed/degraded plugins

### UI: Scraper Page

- Pre-flight panel auto-loads before Run button is used (calls `GET /api/plugins/health`)
- Shows: `✅ N healthy   ⚠️ N degraded   ❌ N failed` + list of failed plugin names
- Run button always enabled (informational, not a hard gate)
- Post-scrape: result panel shows `leads_found`, `duplicates_skipped`, `plugins_skipped`

---

## Files Changed Summary

| File | Action | Why |
|---|---|---|
| `src/plugin_health_monitor.py` | **Create** | New health monitoring service |
| `src/plugins/base_plugin.py` | **Edit** | Add `health_check()` method |
| `src/plugins/*.py` (all 27) | **Edit** | Override `health_check()` with domain HEAD check |
| `src/scraper_orchestrator.py` | **Edit** | Use health monitor, extend scrape_state |
| `src/deduplicator.py` | **Edit** | Add `filter_existing()` DB-aware method |
| `app.py` | **Edit** | New health endpoints, call `filter_existing()`, extend scrape_state |
| `templates/plugins.html` | **Edit** | Status badges + diagnostics button |
| `templates/scraper.html` | **Edit** | Pre-flight panel + extended result display |
| `src/real_stealth_scraper.py` | **Delete** | Superseded + hallucination source |

---

## Out of Scope

- Alerting via email/SMS when plugins go down (future)
- Automatic plugin retry with exponential backoff (future)
- Plugin-level rate limit tuning from UI (future)
