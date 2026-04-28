# Scraper: Plugin Health Monitoring, Deduplication & Anti-Hallucination

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add plugin health monitoring with status badges, DB-aware cross-campaign deduplication, and eliminate all fabricated data from the scraper pipeline.

**Architecture:** A new `PluginHealthMonitor` service owns all health state (lightweight cached checks + on-demand full probes). The `Deduplicator` gains a `filter_existing()` method that cross-references the SQLite DB by email/phone before any lead is saved. All hallucination sources (`real_stealth_scraper.py`) are deleted.

**Tech Stack:** Python 3, Flask, SQLite (sqlite3), requests, concurrent.futures, Jinja2 templates.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `src/real_stealth_scraper.py` | Delete | Remove hallucination source |
| `src/database_manager.py` | Modify | Fix schema: add missing columns (phone, social fields) |
| `src/plugins/base_plugin.py` | Modify | Add `health_check() -> dict` default method |
| `src/plugins/duckduckgo_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/bing_search_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/google_search_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/google_maps_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/yellowpages_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/yelp_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/bbb_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/manta_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/superpages_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/hotfrog_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/whitepages_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/foursquare_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/cylex_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/clutch_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/brownbook_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/youtube_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/reddit_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/trustpilot_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/healthgrades_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/angi_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/thumbtack_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/opencorporates_plugin.py` | Modify | Override `health_check()` with HTTP HEAD |
| `src/plugins/facebook_plugin.py` | Modify | Override `health_check()` — degrade if no session |
| `src/plugins/instagram_plugin.py` | Modify | Override `health_check()` — degrade if no session |
| `src/plugins/linkedin_plugin.py` | Modify | Override `health_check()` — degrade if no session |
| `src/plugins/twitter_plugin.py` | Modify | Override `health_check()` — degrade if no session |
| `src/plugin_health_monitor.py` | Create | Health state cache, lightweight check, full probe |
| `src/deduplicator.py` | Modify | Add `filter_existing()` DB-aware cross-campaign dedup |
| `src/scraper_orchestrator.py` | Modify | Track `_failed_plugins` after each run |
| `app.py` | Modify | Health endpoints, call `filter_existing()`, extend `scrape_state` |
| `templates/plugins.html` | Modify | Status badges per card + "Run Full Diagnostics" button |
| `templates/scraper.html` | Modify | Pre-flight panel + extended result display |
| `tests/test_plugin_health_monitor.py` | Create | Tests for PluginHealthMonitor |
| `tests/test_deduplicator.py` | Modify | Add tests for `filter_existing()` |

---

## Task 1: Delete hallucination source + fix DB schema

The `real_stealth_scraper.py` fabricates pain points via `random.sample(PAIN_POINT_POOLS, 2)`. The `init_db()` schema is also missing columns that `app.py` actually inserts (`phone`, `facebook_url`, `instagram_handle`, `linkedin_url`, `twitter_handle`), causing silent insert failures.

**Files:**
- Delete: `src/real_stealth_scraper.py`
- Modify: `src/database_manager.py`

- [ ] **Step 1: Delete the fabrication source**

```bash
rm /Users/nalinpatel/ai_consulting_business/src/real_stealth_scraper.py
```

- [ ] **Step 2: Fix `init_db()` in `src/database_manager.py`**

Read the file, then replace the `CREATE TABLE IF NOT EXISTS leads` block with the complete schema:

```python
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            website TEXT,
            email TEXT,
            phone TEXT,
            location TEXT,
            niche TEXT,
            leak_amount TEXT,
            pain_points TEXT,
            facebook_url TEXT,
            instagram_handle TEXT,
            linkedin_url TEXT,
            twitter_handle TEXT,
            action TEXT DEFAULT 'READY',
            status TEXT DEFAULT 'Pending'
        )
    ''')
    # Migrate existing DBs that may be missing columns
    for col, col_type in [
        ('phone', 'TEXT'), ('facebook_url', 'TEXT'),
        ('instagram_handle', 'TEXT'), ('linkedin_url', 'TEXT'),
        ('twitter_handle', 'TEXT'),
    ]:
        try:
            cursor.execute(f'ALTER TABLE leads ADD COLUMN {col} {col_type}')
        except Exception:
            pass  # column already exists
```

- [ ] **Step 3: Verify DB initialises cleanly**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -c "from src.database_manager import init_db; init_db(); print('OK')"
```

Expected output: `OK`

- [ ] **Step 4: Commit**

```bash
git add src/database_manager.py && git rm src/real_stealth_scraper.py
git commit -m "fix: add missing DB columns, delete hallucination source"
```

---

## Task 2: Add `health_check()` default to BasePlugin

**Files:**
- Modify: `src/plugins/base_plugin.py`
- Create: `tests/test_base_plugin.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_base_plugin.py`:

```python
from src.plugins.base_plugin import BasePlugin
from src.models.lead import Lead
from typing import List

class MinimalPlugin(BasePlugin):
    name = "minimal"
    def search(self, keyword, location, max_leads) -> List[Lead]:
        return []

def test_default_health_check_returns_healthy():
    p = MinimalPlugin()
    result = p.health_check()
    assert result["status"] == "healthy"
    assert result["error"] is None

def test_health_check_returns_dict_with_required_keys():
    p = MinimalPlugin()
    result = p.health_check()
    assert "status" in result
    assert "error" in result
```

- [ ] **Step 2: Run the test to confirm it fails**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -m pytest tests/test_base_plugin.py -v 2>&1 | head -30
```

Expected: `AttributeError: 'MinimalPlugin' object has no attribute 'health_check'`

- [ ] **Step 3: Add `health_check()` to `src/plugins/base_plugin.py`**

Replace the entire file content:

```python
from abc import ABC, abstractmethod
from typing import List
from src.models.lead import Lead

class BasePlugin(ABC):
    name: str = ""
    requires_auth: bool = False
    rate_limit_seconds: float = 2.0

    @abstractmethod
    def search(self, keyword: str, location: str, max_leads: int) -> List[Lead]:
        pass

    def is_available(self) -> bool:
        return True

    def health_check(self) -> dict:
        return {"status": "healthy", "error": None}
```

- [ ] **Step 4: Run the test to confirm it passes**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -m pytest tests/test_base_plugin.py -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/plugins/base_plugin.py tests/test_base_plugin.py
git commit -m "feat: add health_check() default to BasePlugin"
```

---

## Task 3: Override `health_check()` in non-auth plugins (22 plugins)

Each plugin does an HTTP HEAD request to its target domain. Status < 500 = healthy, >= 500 or exception = failed. `state_registry_plugin` has no single domain so keeps the default from BasePlugin.

**Pattern** (apply to each plugin below with its specific target URL):

```python
import requests

_HC_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# add this method to the plugin class:
def health_check(self) -> dict:
    try:
        r = requests.head('https://TARGET_DOMAIN_HERE', timeout=5,
                          headers=_HC_HEADERS, allow_redirects=True)
        if r.status_code < 500:
            return {"status": "healthy", "error": None}
        return {"status": "failed", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"status": "failed", "error": str(e)[:120]}
```

**Plugin to target domain mapping:**

| Plugin file | Target URL for health_check |
|---|---|
| `duckduckgo_plugin.py` | `https://html.duckduckgo.com` |
| `bing_search_plugin.py` | `https://www.bing.com` |
| `google_search_plugin.py` | `https://www.google.com` |
| `google_maps_plugin.py` | `https://maps.google.com` |
| `yellowpages_plugin.py` | `https://www.yellowpages.com` |
| `yelp_plugin.py` | `https://www.yelp.com` |
| `bbb_plugin.py` | `https://www.bbb.org` |
| `manta_plugin.py` | `https://www.manta.com` |
| `superpages_plugin.py` | `https://www.superpages.com` |
| `hotfrog_plugin.py` | `https://www.hotfrog.com` |
| `whitepages_plugin.py` | `https://www.whitepages.com` |
| `foursquare_plugin.py` | `https://foursquare.com` |
| `cylex_plugin.py` | `https://www.cylex-usa.com` |
| `clutch_plugin.py` | `https://clutch.co` |
| `brownbook_plugin.py` | `https://www.brownbook.net` |
| `youtube_plugin.py` | `https://www.youtube.com` |
| `reddit_plugin.py` | `https://www.reddit.com` |
| `trustpilot_plugin.py` | `https://www.trustpilot.com` |
| `healthgrades_plugin.py` | `https://www.healthgrades.com` |
| `angi_plugin.py` | `https://www.angi.com` |
| `thumbtack_plugin.py` | `https://www.thumbtack.com` |
| `opencorporates_plugin.py` | `https://opencorporates.com` |

Note: `duckduckgo_plugin.py` already has a `_HEADERS` dict — use it in `health_check()` instead of declaring `_HC_HEADERS`.

**Files:**
- Modify: all 22 plugin files listed above (do NOT modify `state_registry_plugin.py`)

- [ ] **Step 1: Write a test that verifies the override exists and works**

Create `tests/test_plugin_health_checks.py`:

```python
from unittest.mock import patch, MagicMock
import pytest

def _make_response(status_code):
    r = MagicMock()
    r.status_code = status_code
    return r

def test_duckduckgo_health_check_healthy():
    from src.plugins.duckduckgo_plugin import DuckDuckGoPlugin
    p = DuckDuckGoPlugin()
    with patch('requests.head', return_value=_make_response(200)):
        result = p.health_check()
    assert result['status'] == 'healthy'
    assert result['error'] is None

def test_duckduckgo_health_check_failed_on_500():
    from src.plugins.duckduckgo_plugin import DuckDuckGoPlugin
    p = DuckDuckGoPlugin()
    with patch('requests.head', return_value=_make_response(503)):
        result = p.health_check()
    assert result['status'] == 'failed'
    assert '503' in result['error']

def test_duckduckgo_health_check_failed_on_exception():
    from src.plugins.duckduckgo_plugin import DuckDuckGoPlugin
    p = DuckDuckGoPlugin()
    with patch('requests.head', side_effect=Exception('connection refused')):
        result = p.health_check()
    assert result['status'] == 'failed'
    assert 'connection refused' in result['error']

def test_yelp_health_check_healthy():
    from src.plugins.yelp_plugin import YelpPlugin
    p = YelpPlugin()
    with patch('requests.head', return_value=_make_response(200)):
        result = p.health_check()
    assert result['status'] == 'healthy'

def test_google_maps_health_check_healthy():
    from src.plugins.google_maps_plugin import GoogleMapsPlugin
    p = GoogleMapsPlugin()
    with patch('requests.head', return_value=_make_response(200)):
        result = p.health_check()
    assert result['status'] == 'healthy'
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -m pytest tests/test_plugin_health_checks.py -v 2>&1 | head -20
```

Expected: the 500 and exception tests fail since base `health_check()` returns `healthy` regardless.

- [ ] **Step 3: Add `health_check()` to each of the 22 non-auth plugins**

For each plugin in the table above, add:
1. `import requests` at the top if not already present
2. `_HC_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}` if the file doesn't already have a headers dict
3. The `health_check()` method in the class body using the target URL from the table

Example for `duckduckgo_plugin.py` — the method to add inside `DuckDuckGoPlugin`:

```python
def health_check(self) -> dict:
    try:
        r = requests.head('https://html.duckduckgo.com', timeout=5,
                          headers=_HEADERS, allow_redirects=True)
        if r.status_code < 500:
            return {"status": "healthy", "error": None}
        return {"status": "failed", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"status": "failed", "error": str(e)[:120]}
```

For the remaining 21 plugins, the method is identical except the target URL. Use `_HEADERS` if the file already defines it (many do), otherwise use `_HC_HEADERS`.

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -m pytest tests/test_plugin_health_checks.py -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/plugins/ tests/test_plugin_health_checks.py
git commit -m "feat: add health_check() to all non-auth scraper plugins"
```

---

## Task 4: Override `health_check()` in auth-required social plugins

Social plugins (facebook, instagram, linkedin, twitter) use `SessionManager` for auth. `health_check()` returns `degraded` (not `failed`) when no session exists — because missing credentials is expected, not a malfunction.

**Files:**
- Modify: `src/plugins/facebook_plugin.py`, `instagram_plugin.py`, `linkedin_plugin.py`, `twitter_plugin.py`

- [ ] **Step 1: Add tests for social plugin health checks**

Append to `tests/test_plugin_health_checks.py`:

```python
def test_facebook_health_check_degraded_when_no_session():
    from src.plugins.facebook_plugin import FacebookPlugin
    from src.session_manager import SessionManager
    sm = MagicMock(spec=SessionManager)
    sm.is_authenticated.return_value = False
    p = FacebookPlugin(sm)
    result = p.health_check()
    assert result['status'] == 'degraded'
    assert 'credentials' in result['error'].lower()

def test_facebook_health_check_healthy_when_session_exists():
    from src.plugins.facebook_plugin import FacebookPlugin
    from src.session_manager import SessionManager
    sm = MagicMock(spec=SessionManager)
    sm.is_authenticated.return_value = True
    p = FacebookPlugin(sm)
    result = p.health_check()
    assert result['status'] == 'healthy'
    assert result['error'] is None
```

- [ ] **Step 2: Run to confirm they fail**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -m pytest tests/test_plugin_health_checks.py::test_facebook_health_check_degraded_when_no_session tests/test_plugin_health_checks.py::test_facebook_health_check_healthy_when_session_exists -v
```

Expected: `FAILED` — `FacebookPlugin` has no `health_check()` override yet (base always returns healthy).

- [ ] **Step 3: Add `health_check()` to `src/plugins/facebook_plugin.py`**

Add this method inside the `FacebookPlugin` class, after `is_available()`:

```python
def health_check(self) -> dict:
    if not self._sessions.is_authenticated(self.name):
        return {"status": "degraded", "error": "missing credentials — add session via Settings"}
    return {"status": "healthy", "error": None}
```

- [ ] **Step 4: Add the same `health_check()` to the remaining three social plugins**

In `instagram_plugin.py` (class `InstagramPlugin`) — read the file first to confirm `self._sessions` is the attribute name, then add:
```python
def health_check(self) -> dict:
    if not self._sessions.is_authenticated(self.name):
        return {"status": "degraded", "error": "missing credentials — add session via Settings"}
    return {"status": "healthy", "error": None}
```

In `linkedin_plugin.py` (class `LinkedInPlugin`) — same method.

In `twitter_plugin.py` (class `TwitterPlugin`) — same method.

- [ ] **Step 5: Run all health check tests**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -m pytest tests/test_plugin_health_checks.py -v
```

Expected: all `PASSED`

- [ ] **Step 6: Commit**

```bash
git add src/plugins/facebook_plugin.py src/plugins/instagram_plugin.py src/plugins/linkedin_plugin.py src/plugins/twitter_plugin.py tests/test_plugin_health_checks.py
git commit -m "feat: add health_check() to social plugins — degrade when no session"
```

---

## Task 5: Create `PluginHealthMonitor`

**Files:**
- Create: `src/plugin_health_monitor.py`
- Create: `tests/test_plugin_health_monitor.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_plugin_health_monitor.py`:

```python
import json
import os
import pytest
from unittest.mock import MagicMock, patch
from src.plugins.base_plugin import BasePlugin
from src.models.lead import Lead

def make_plugin(name, health_result, leads=None):
    p = MagicMock(spec=BasePlugin)
    p.name = name
    p.health_check.return_value = health_result
    p.search.return_value = leads or [Lead(business_name="Test", city="NYC", state="NY", sources=[name])]
    return p

def test_lightweight_check_marks_healthy_plugin(tmp_path):
    from src.plugin_health_monitor import PluginHealthMonitor
    p = make_plugin("duckduckgo", {"status": "healthy", "error": None})
    monitor = PluginHealthMonitor([p], cache_path=str(tmp_path / "health.json"))
    result = monitor.run_lightweight_check()
    assert result["duckduckgo"]["status"] == "healthy"
    assert result["duckduckgo"]["error"] is None

def test_lightweight_check_marks_failed_plugin(tmp_path):
    from src.plugin_health_monitor import PluginHealthMonitor
    p = make_plugin("yelp", {"status": "failed", "error": "HTTP 403"})
    monitor = PluginHealthMonitor([p], cache_path=str(tmp_path / "health.json"))
    result = monitor.run_lightweight_check()
    assert result["yelp"]["status"] == "failed"
    assert "403" in result["yelp"]["error"]

def test_lightweight_check_marks_degraded_plugin(tmp_path):
    from src.plugin_health_monitor import PluginHealthMonitor
    p = make_plugin("facebook", {"status": "degraded", "error": "missing credentials"})
    monitor = PluginHealthMonitor([p], cache_path=str(tmp_path / "health.json"))
    result = monitor.run_lightweight_check()
    assert result["facebook"]["status"] == "degraded"

def test_cache_is_persisted_to_file(tmp_path):
    from src.plugin_health_monitor import PluginHealthMonitor
    cache_file = str(tmp_path / "health.json")
    p = make_plugin("bing_search", {"status": "healthy", "error": None})
    monitor = PluginHealthMonitor([p], cache_path=cache_file)
    monitor.run_lightweight_check()
    assert os.path.exists(cache_file)
    with open(cache_file) as f:
        data = json.load(f)
    assert "bing_search" in data

def test_cache_ttl_not_rechecked_within_ttl(tmp_path):
    from src.plugin_health_monitor import PluginHealthMonitor
    p = make_plugin("duckduckgo", {"status": "healthy", "error": None})
    monitor = PluginHealthMonitor([p], cache_path=str(tmp_path / "health.json"))
    monitor.run_lightweight_check()
    monitor.run_lightweight_check()
    assert p.health_check.call_count == 1  # only called once — second call uses cache

def test_get_healthy_plugin_names(tmp_path):
    from src.plugin_health_monitor import PluginHealthMonitor
    p1 = make_plugin("duckduckgo", {"status": "healthy", "error": None})
    p2 = make_plugin("yelp", {"status": "failed", "error": "403"})
    p3 = make_plugin("facebook", {"status": "degraded", "error": "no creds"})
    monitor = PluginHealthMonitor([p1, p2, p3], cache_path=str(tmp_path / "health.json"))
    monitor.run_lightweight_check()
    names = monitor.get_healthy_plugin_names()
    assert names == ["duckduckgo"]
    assert "yelp" not in names
    assert "facebook" not in names

def test_get_summary(tmp_path):
    from src.plugin_health_monitor import PluginHealthMonitor
    p1 = make_plugin("a", {"status": "healthy", "error": None})
    p2 = make_plugin("b", {"status": "failed", "error": "err"})
    p3 = make_plugin("c", {"status": "degraded", "error": "creds"})
    monitor = PluginHealthMonitor([p1, p2, p3], cache_path=str(tmp_path / "health.json"))
    monitor.run_lightweight_check()
    summary = monitor.get_summary()
    assert summary["healthy"] == 1
    assert summary["failed"] == 1
    assert summary["degraded"] == 1
```

- [ ] **Step 2: Run to confirm they all fail**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -m pytest tests/test_plugin_health_monitor.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'src.plugin_health_monitor'`

- [ ] **Step 3: Create `src/plugin_health_monitor.py`**

```python
import json
import os
import concurrent.futures
from datetime import datetime, timezone
from typing import Dict, List
from src.plugins.base_plugin import BasePlugin

CACHE_TTL_SECONDS = 300  # 5 minutes


class PluginHealthMonitor:
    def __init__(self, plugins: List[BasePlugin], cache_path: str = "data/plugin_health.json"):
        self._plugins: Dict[str, BasePlugin] = {p.name: p for p in plugins}
        self._cache_path = cache_path
        self._cache: Dict[str, dict] = self._load_cache()

    def _load_cache(self) -> Dict[str, dict]:
        if os.path.exists(self._cache_path):
            try:
                with open(self._cache_path) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_cache(self):
        os.makedirs(os.path.dirname(self._cache_path) or ".", exist_ok=True)
        with open(self._cache_path, "w") as f:
            json.dump(self._cache, f, indent=2)

    def _is_fresh(self, entry: dict) -> bool:
        checked_at = entry.get("checked_at")
        if not checked_at:
            return False
        try:
            checked = datetime.fromisoformat(checked_at)
            if checked.tzinfo is None:
                checked = checked.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - checked).total_seconds()
            return age < CACHE_TTL_SECONDS
        except Exception:
            return False

    def _record(self, name: str, result: dict):
        self._cache[name] = {
            "status": result["status"],
            "error": result.get("error"),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def run_lightweight_check(self) -> Dict[str, dict]:
        for name, plugin in self._plugins.items():
            if name in self._cache and self._is_fresh(self._cache[name]):
                continue
            try:
                result = plugin.health_check()
            except Exception as e:
                result = {"status": "failed", "error": str(e)[:120]}
            self._record(name, result)
        self._save_cache()
        return self._cache

    def run_full_probe(self) -> Dict[str, dict]:
        def probe(name: str, plugin: BasePlugin):
            try:
                leads = plugin.search("dentist", "New York", 1)
                if leads:
                    return name, {"status": "healthy", "error": None}
                return name, {"status": "failed", "error": "returned 0 results"}
            except Exception as e:
                return name, {"status": "failed", "error": str(e)[:120]}

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self._plugins)) as ex:
            futures = {ex.submit(probe, n, p): n for n, p in self._plugins.items()}
            for future in concurrent.futures.as_completed(futures, timeout=35):
                try:
                    name, result = future.result()
                    self._record(name, result)
                except Exception:
                    pass
        self._save_cache()
        return self._cache

    def get_status(self) -> Dict[str, dict]:
        return dict(self._cache)

    def get_healthy_plugin_names(self) -> List[str]:
        return [
            name for name, entry in self._cache.items()
            if entry.get("status") == "healthy"
        ]

    def get_summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {"healthy": 0, "degraded": 0, "failed": 0, "unknown": 0}
        for name in self._plugins:
            entry = self._cache.get(name)
            status = entry["status"] if entry else "unknown"
            counts[status] = counts.get(status, 0) + 1
        return counts
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -m pytest tests/test_plugin_health_monitor.py -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/plugin_health_monitor.py tests/test_plugin_health_monitor.py
git commit -m "feat: add PluginHealthMonitor with lightweight check, full probe, and cache"
```

---

## Task 6: Add `filter_existing()` to Deduplicator

This method queries the SQLite DB for all known emails and phones, then filters out any lead whose email or phone already exists. Returns `(new_leads, skipped_count)`.

**Files:**
- Modify: `src/deduplicator.py`
- Modify: `tests/test_deduplicator.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_deduplicator.py`:

```python
import sqlite3
import tempfile
import os

def _make_db_with_leads(leads_data):
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    with sqlite3.connect(tmp.name) as conn:
        conn.execute('''CREATE TABLE leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT, phone TEXT
        )''')
        for email, phone in leads_data:
            conn.execute('INSERT INTO leads (email, phone) VALUES (?, ?)', (email, phone))
    return tmp.name

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
    assert len(new_leads) == 1  # fails safe — don't block on DB error
    assert skipped == 0
```

- [ ] **Step 2: Run to confirm they fail**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -m pytest tests/test_deduplicator.py::test_filter_existing_removes_duplicate_email -v 2>&1 | head -20
```

Expected: `AttributeError: 'Deduplicator' object has no attribute 'filter_existing'`

- [ ] **Step 3: Add `filter_existing()` to `src/deduplicator.py`**

Append this method to the `Deduplicator` class (after `_merge_into`):

```python
def filter_existing(self, leads: List[Lead], db_path: str):
    import sqlite3
    try:
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(
                "SELECT email, phone FROM leads WHERE email IS NOT NULL OR phone IS NOT NULL"
            ).fetchall()
    except Exception:
        return leads, 0

    known_emails = {r[0].lower() for r in rows if r[0]}
    known_phones = {r[1] for r in rows if r[1]}

    new_leads = []
    skipped = 0
    for lead in leads:
        is_dup = (
            (lead.email and lead.email.lower() in known_emails) or
            (lead.phone and lead.phone in known_phones)
        )
        if is_dup:
            skipped += 1
        else:
            new_leads.append(lead)
    return new_leads, skipped
```

- [ ] **Step 4: Run all deduplicator tests**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -m pytest tests/test_deduplicator.py -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/deduplicator.py tests/test_deduplicator.py
git commit -m "feat: add filter_existing() to Deduplicator for cross-campaign dedup by email/phone"
```

---

## Task 7: Update ScraperOrchestrator to track runtime failures

When a plugin throws during the actual scrape, its name is recorded in `failed_plugins`. This lets `app.py` update the health monitor cache after the run.

**Files:**
- Modify: `src/scraper_orchestrator.py`
- Modify: `tests/test_orchestrator.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_orchestrator.py`:

```python
def test_failed_plugins_are_tracked():
    p1 = make_plugin("yelp", [Lead(business_name="Good Biz", city="NYC", state="NY",
                                    sources=["yelp"], email="a@b.com")])
    p2 = make_plugin("bbb", [])
    p2.search.side_effect = Exception("connection timeout")
    orch = ScraperOrchestrator(plugins=[p1, p2])
    orch.scrape("dentist", "NYC, NY", max_leads=10)
    assert "bbb" in orch.failed_plugins
    assert "yelp" not in orch.failed_plugins
```

- [ ] **Step 2: Run to confirm it fails**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -m pytest tests/test_orchestrator.py::test_failed_plugins_are_tracked -v 2>&1 | head -20
```

Expected: `AttributeError: 'ScraperOrchestrator' object has no attribute 'failed_plugins'`

- [ ] **Step 3: Update `src/scraper_orchestrator.py`**

Replace the `__init__` and `scrape` methods:

```python
def __init__(self, plugins: List[BasePlugin]):
    self._plugins = [p for p in plugins if p.is_available()]
    self._deduplicator = Deduplicator(total_plugins=max(len(plugins), 1))
    self._enricher = WebsiteEnricher()
    self._rate_limiter = RateLimiter(RATE_CONFIG)
    self.failed_plugins: List[str] = []

def scrape(self, keyword: str, location: str, max_leads: int = 50, on_progress=None) -> List[Lead]:
    self.failed_plugins = []
    if not self._plugins:
        return []
    per_plugin = max(5, max_leads // len(self._plugins))
    all_leads: List[Lead] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(self._plugins)) as ex:
        futures = {
            ex.submit(self._run_plugin, p, keyword, location, per_plugin): p.name
            for p in self._plugins
        }
        for future in concurrent.futures.as_completed(futures):
            plugin_name = futures[future]
            try:
                leads = future.result(timeout=120)
                all_leads.extend(leads)
                logger.info(f"{plugin_name}: {len(leads)} leads")
                if on_progress:
                    on_progress(plugin_name, len(all_leads))
            except Exception as e:
                logger.warning(f"{plugin_name} failed: {e}")
                self.failed_plugins.append(plugin_name)

    merged = self._deduplicator.deduplicate(all_leads)
    enriched = [self._enricher.enrich(lead) for lead in merged]
    return self._score(enriched)[:max_leads]
```

- [ ] **Step 4: Run all orchestrator tests**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -m pytest tests/test_orchestrator.py -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/scraper_orchestrator.py tests/test_orchestrator.py
git commit -m "feat: track failed plugins in ScraperOrchestrator.failed_plugins"
```

---

## Task 8: Add health endpoints to `app.py` + update scrape thread

Add `GET /api/plugins/health` and `POST /api/plugins/diagnose` endpoints. Update the scrape `run()` thread to run a lightweight health check, skip non-healthy plugins, call `filter_existing()` before saving, and extend `scrape_state` with the new fields.

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_app_routes.py`:

```python
def test_health_endpoint_redirects_unauthenticated(client):
    resp = client.get('/api/plugins/health')
    assert resp.status_code in (302, 308)

def test_diagnose_endpoint_redirects_unauthenticated(client):
    resp = client.post('/api/plugins/diagnose')
    assert resp.status_code in (302, 308)
```

- [ ] **Step 2: Run to confirm they fail (expect 404, not 302)**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -m pytest tests/test_app_routes.py::test_health_endpoint_redirects_unauthenticated tests/test_app_routes.py::test_diagnose_endpoint_redirects_unauthenticated -v
```

Expected: `FAILED` — endpoints do not exist (404).

- [ ] **Step 3: Add the global health monitor helper + extend `scrape_state` in `app.py`**

After `load_dotenv()` at the top of `app.py`, add:

```python
_health_monitor = None

def _get_health_monitor():
    global _health_monitor
    if _health_monitor is None:
        from src.plugins.plugin_factory import build_plugins
        from src.plugin_health_monitor import PluginHealthMonitor
        _health_monitor = PluginHealthMonitor(build_plugins())
    return _health_monitor
```

Replace the `scrape_state` dict with:

```python
scrape_state = {
    'running': False, 'progress': 0,
    'leads_found': 0, 'duplicates_skipped': 0,
    'plugins_run': 0, 'plugins_skipped': [],
    'current_plugin': '', 'error': None
}
```

- [ ] **Step 4: Add the two new endpoints to `app.py`** (add after the existing `/api/plugins/toggle` endpoint):

```python
@app.route('/api/plugins/health')
@login_required
def plugins_health():
    monitor = _get_health_monitor()
    cache = monitor.run_lightweight_check()
    return jsonify({'summary': monitor.get_summary(), 'plugins': cache})


@app.route('/api/plugins/diagnose', methods=['POST'])
@login_required
def plugins_diagnose():
    def run_probe():
        _get_health_monitor().run_full_probe()
    threading.Thread(target=run_probe, daemon=True).start()
    return jsonify({'status': 'probe started'})
```

- [ ] **Step 5: Update the scrape `run()` closure in `app.py`**

Inside the `run()` function (within the `/api/scrape` route), make these targeted changes:

After `plugins_list = build_plugins()`, add:

```python
from src.plugin_health_monitor import PluginHealthMonitor
from src.database_manager import DB_PATH as _DB_PATH

monitor = PluginHealthMonitor(plugins_list)
monitor.run_lightweight_check()
healthy_names = set(monitor.get_healthy_plugin_names())
skipped_names = [p.name for p in plugins_list if p.name not in healthy_names]
active_plugins = [p for p in plugins_list if p.name in healthy_names]
scrape_state['plugins_skipped'] = skipped_names
scrape_state['plugins_run'] = len(active_plugins)
orch = ScraperOrchestrator(active_plugins)
```

Remove the existing `orch = ScraperOrchestrator(plugins_list)` line (replaced above).

After `results = orch.scrape(keyword, location, max_leads, on_progress=on_progress)`, add:

```python
# Record any plugins that failed at runtime
import datetime as _dt
for failed_name in orch.failed_plugins:
    monitor._cache[failed_name] = {
        'status': 'failed',
        'error': 'failed during scrape run',
        'checked_at': _dt.datetime.now(_dt.timezone.utc).isoformat()
    }
monitor._save_cache()
```

After the contact filter (`results = [l for l in results if any([...])]`), add:

```python
from src.deduplicator import Deduplicator as _Dedup
results, dupes_skipped = _Dedup().filter_existing(results, _DB_PATH)
scrape_state['duplicates_skipped'] = dupes_skipped
```

Replace the final `scrape_state.update(...)` call with:

```python
scrape_state.update({
    'running': False, 'progress': 100,
    'leads_found': len(results),
    'duplicates_skipped': dupes_skipped,
    'plugins_run': len(active_plugins),
    'plugins_skipped': skipped_names,
    'current_plugin': 'Done'
})
```

- [ ] **Step 6: Run all app route tests**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -m pytest tests/test_app_routes.py -v
```

Expected: all `PASSED`

- [ ] **Step 7: Commit**

```bash
git add app.py tests/test_app_routes.py
git commit -m "feat: add /api/plugins/health and /api/plugins/diagnose, integrate health filtering and cross-campaign dedup into scrape thread"
```

---

## Task 9: Update `templates/plugins.html` with status badges + diagnostics button

**Files:**
- Modify: `templates/plugins.html`

- [ ] **Step 1: Replace `templates/plugins.html`** with the updated version below.

Key changes: add a status dot `span` per card; add a "Run Full Diagnostics" button; load health status asynchronously via `fetch`. The `togglePlugin` function is unchanged.

Note: all DOM updates use `textContent` (not `innerHTML`) to avoid XSS. The dot color is set via `style.background` (a safe property).

```html
{% extends "base.html" %}
{% block page_title %}Plugins{% endblock %}
{% block heading %}Plugins{% endblock %}
{% block actions %}
  <span id="save-status" style="font-size:12px;color:#15803d"></span>
  <button class="btn btn-secondary" id="diagnose-btn" onclick="runDiagnostics()"
          style="margin-left:12px;font-size:12px">Run Full Diagnostics</button>
  <span id="diag-status" style="font-size:12px;color:#64748b;margin-left:8px"></span>
{% endblock %}

{% block content %}
{% for group_name, plugin_names in plugin_groups.items() %}
<div class="plugin-section-label">{{ group_name }}</div>
<div class="plugin-grid">
  {% for pname in plugin_names %}
  {% set enabled = config.get(pname, {}).get('enabled', false) %}
  <div class="plugin-card {% if enabled %}enabled{% endif %}" id="card-{{ pname }}">
    <span class="health-dot" id="dot-{{ pname }}" style="
      display:inline-block;width:8px;height:8px;border-radius:50%;
      background:#94a3b8;margin-right:6px;vertical-align:middle;cursor:default;
    "></span>
    <span>{{ pname | replace('_', ' ') | title }}</span>
    <label class="toggle-wrap">
      <input type="checkbox" {% if enabled %}checked{% endif %}
        onchange="togglePlugin('{{ pname }}', this.checked, this)">
      <span class="toggle-slider"></span>
    </label>
  </div>
  {% endfor %}
</div>
{% endfor %}

<div class="alert alert-info" style="margin-top:16px">
  &#128161; Social plugins (Facebook, Instagram, LinkedIn, Twitter) require credentials.
  Add them in <a href="{{ url_for('settings') }}" style="color:#1d4ed8">Settings &#8594;</a>
</div>
{% endblock %}

{% block scripts %}
<script>
const STATUS_COLORS = {
  healthy: '#16a34a', degraded: '#ca8a04', failed: '#dc2626', unknown: '#94a3b8'
};

function applyHealthResults(plugins) {
  Object.keys(plugins).forEach(function(name) {
    var info = plugins[name];
    var dot = document.getElementById('dot-' + name);
    if (!dot) return;
    dot.style.background = STATUS_COLORS[info.status] || STATUS_COLORS.unknown;
    dot.title = info.error ? (info.status + ': ' + info.error) : info.status;
  });
}

async function loadHealthStatus() {
  try {
    var r = await fetch('/api/plugins/health');
    var data = await r.json();
    if (data.plugins) applyHealthResults(data.plugins);
  } catch (e) { /* non-blocking */ }
}

async function runDiagnostics() {
  var btn = document.getElementById('diagnose-btn');
  var statusEl = document.getElementById('diag-status');
  btn.disabled = true;
  statusEl.textContent = 'Running full probe (30s)…';
  await fetch('/api/plugins/diagnose', { method: 'POST' });
  setTimeout(async function() {
    await loadHealthStatus();
    statusEl.textContent = 'Done';
    btn.disabled = false;
    setTimeout(function() { statusEl.textContent = ''; }, 3000);
  }, 32000);
}

async function togglePlugin(name, enabled, checkbox) {
  var r = await fetch('/api/plugins/toggle', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({plugin: name, enabled: enabled})
  });
  var data = await r.json();
  var card = document.getElementById('card-' + name);
  if (data.status === 'success') {
    card.classList.toggle('enabled', enabled);
    var msg = document.getElementById('save-status');
    msg.textContent = 'Saved';
    setTimeout(function() { msg.textContent = ''; }, 2000);
  } else {
    checkbox.checked = !enabled;
    alert('Failed: ' + data.message);
  }
}

loadHealthStatus();
</script>
{% endblock %}
```

- [ ] **Step 2: Start the dev server and verify visually**

```bash
cd /Users/nalinpatel/ai_consulting_business && python app.py
```

Open `http://localhost:5001` — log in, navigate to `/plugins`.
Verify:
- Each plugin card shows a grey dot that changes to green/yellow/red after health call returns
- "Run Full Diagnostics" button is visible in the header actions area
- Hovering a dot shows the status text in the browser tooltip (`title` attribute)

Press Ctrl+C to stop server.

- [ ] **Step 3: Commit**

```bash
git add templates/plugins.html
git commit -m "feat: add health status badges and Run Full Diagnostics button to plugins page"
```

---

## Task 10: Update `templates/scraper.html` with pre-flight panel + extended result display

**Files:**
- Modify: `templates/scraper.html`

- [ ] **Step 1: Replace `templates/scraper.html`** with the updated version.

Key changes: add a "Plugin Status" card at the top that loads via `fetch`; extend the post-scrape result text to show `plugins_run`, `plugins_skipped`, and `duplicates_skipped`. All DOM writes use `textContent`.

```html
{% extends "base.html" %}
{% block page_title %}Scraper{% endblock %}
{% block heading %}Scraper{% endblock %}

{% block content %}
<div class="card" id="preflight-card">
  <div class="card-header"><h3>Plugin Status</h3></div>
  <div class="card-body">
    <div id="preflight-summary" style="font-size:13px;color:#64748b">Checking plugins&hellip;</div>
    <div id="preflight-failed" style="font-size:12px;color:#b91c1c;margin-top:4px"></div>
  </div>
</div>

<div class="card">
  <div class="card-header"><h3>New Campaign</h3></div>
  <div class="card-body">
    <form id="scrape-form">
      <div class="form-row-3">
        <div class="form-group">
          <label>Industry / Niche</label>
          <input type="text" name="keyword" value="Dentist"
                 placeholder="e.g. Dentist, Roofing, Yoga&hellip;" required>
        </div>
        <div class="form-group">
          <label>Location</label>
          <input type="text" name="location" value="California"
                 placeholder="City, State or 'nationwide'" required>
        </div>
        <div class="form-group">
          <label>Max Leads</label>
          <select name="max_leads">
            <option value="50">50</option>
            <option value="100">100</option>
            <option value="200">200</option>
            <option value="500">500</option>
          </select>
        </div>
      </div>
      <button type="submit" class="btn btn-primary" id="run-btn">&#9654; Run Campaign</button>
    </form>
  </div>
</div>

<div class="card" id="progress-card" style="display:none">
  <div class="card-header">
    <h3>Live Progress</h3>
    <span id="status-text" style="font-size:12px;color:#64748b">Starting&hellip;</span>
  </div>
  <div class="card-body">
    <div style="display:flex;justify-content:space-between;margin-bottom:6px;font-size:12px;color:#475569">
      <span id="plugin-label">Initialising plugins&hellip;</span>
      <span id="lead-count">0 leads found</span>
    </div>
    <div class="progress-bar">
      <div class="progress-fill" id="progress-fill" style="width:0%"></div>
    </div>
    <div id="result-detail" style="font-size:12px;color:#475569;margin-top:8px"></div>
  </div>
</div>
{% endblock %}

{% block scripts %}
<script>
var pollInterval = null;

async function loadPreFlight() {
  try {
    var r = await fetch('/api/plugins/health');
    var data = await r.json();
    var s = data.summary || {};
    var healthy = s.healthy || 0;
    var degraded = s.degraded || 0;
    var failed = s.failed || 0;
    var total = healthy + degraded + failed + (s.unknown || 0);
    document.getElementById('preflight-summary').textContent =
      healthy + ' healthy  |  ' + degraded + ' degraded  |  ' + failed + ' failed  (' + total + ' total)';
    var failedNames = [];
    var plugins = data.plugins || {};
    Object.keys(plugins).forEach(function(k) {
      if (plugins[k].status === 'failed') failedNames.push(k);
    });
    if (failedNames.length) {
      document.getElementById('preflight-failed').textContent =
        'Failed plugins (will be skipped): ' + failedNames.join(', ');
    }
  } catch (e) {
    document.getElementById('preflight-summary').textContent = 'Could not load plugin status.';
  }
}

function startPolling() {
  if (pollInterval) return;
  var btn = document.getElementById('run-btn');
  btn.disabled = true;
  btn.textContent = 'Running…';
  document.getElementById('progress-card').style.display = 'block';

  pollInterval = setInterval(async function() {
    var r = await fetch('/api/scrape/status');
    var s = await r.json();
    document.getElementById('progress-fill').style.width = s.progress + '%';
    document.getElementById('lead-count').textContent = s.leads_found + ' leads found';
    document.getElementById('plugin-label').textContent = s.current_plugin || 'Running…';
    if (!s.running) {
      clearInterval(pollInterval);
      pollInterval = null;
      btn.disabled = false;
      btn.textContent = '▶ Run Campaign';
      if (s.error) {
        document.getElementById('status-text').textContent = 'Error: ' + s.error;
        document.getElementById('status-text').style.color = '#b91c1c';
      } else if (s.progress > 0) {
        document.getElementById('status-text').textContent =
          'Done — ' + s.leads_found + ' leads saved';
        document.getElementById('status-text').style.color = '#15803d';
        var skippedPart = (s.plugins_skipped && s.plugins_skipped.length)
          ? ' | Skipped: ' + s.plugins_skipped.join(', ') : '';
        var dupesPart = s.duplicates_skipped
          ? ' | ' + s.duplicates_skipped + ' duplicates discarded' : '';
        document.getElementById('result-detail').textContent =
          'Plugins run: ' + (s.plugins_run || 0) + skippedPart + dupesPart;
      }
    }
  }, 2000);
}

fetch('/api/scrape/status').then(function(r) { return r.json(); }).then(function(s) {
  if (s.running) {
    document.getElementById('status-text').textContent = 'Resuming…';
    document.getElementById('progress-fill').style.width = s.progress + '%';
    document.getElementById('lead-count').textContent = s.leads_found + ' leads found';
    document.getElementById('plugin-label').textContent = s.current_plugin || 'Running…';
    startPolling();
  }
});

document.getElementById('scrape-form').addEventListener('submit', async function(e) {
  e.preventDefault();
  document.getElementById('status-text').textContent = 'Starting…';
  document.getElementById('status-text').style.color = '#64748b';
  document.getElementById('result-detail').textContent = '';
  await fetch('/api/scrape', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      keyword: this.keyword.value,
      location: this.location.value,
      max_leads: parseInt(this.max_leads.value)
    })
  });
  startPolling();
});

loadPreFlight();
</script>
{% endblock %}
```

- [ ] **Step 2: Start the dev server and verify visually**

```bash
cd /Users/nalinpatel/ai_consulting_business && python app.py
```

Open `http://localhost:5001/scraper` after logging in.
Verify:
- "Plugin Status" card appears at the top with counts like `22 healthy | 3 degraded | 2 failed (27 total)`
- Failed plugin names appear in red below the counts
- After a scrape completes, the result-detail line shows `Plugins run: N | Skipped: ... | N duplicates discarded`

Press Ctrl+C to stop server.

- [ ] **Step 3: Commit**

```bash
git add templates/scraper.html
git commit -m "feat: add pre-flight plugin status panel and extended result display to scraper page"
```

---

## Task 11: Full test suite + push

- [ ] **Step 1: Run the complete test suite**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -m pytest tests/ -v 2>&1 | tail -40
```

Expected: all new tests pass. Note any pre-existing failures (do not fix them here).

- [ ] **Step 2: Push to GitHub**

```bash
git push origin main
```

---

## Spec Coverage Check

| Spec requirement | Covered in task |
|---|---|
| Plugin failure alerting — report which plugins are down | Tasks 5, 8, 9, 10 |
| Diagnostic checks before every search (lightweight) | Task 8 (scrape thread) |
| On-demand full probe (Run Diagnostics button) | Tasks 5, 8, 9 |
| Continuous monitoring — track failures during runtime | Tasks 7, 8 |
| Zero-hallucination — no fabricated data | Task 1 (delete real_stealth_scraper.py) |
| Contact data validation gate | Existing filter in app.py (kept, no change needed) |
| Global deduplication by email/phone | Tasks 6, 8 |
| Cross-campaign exclusion (all historical records) | Task 6 (queries full leads table) |
| Plugin cards show green/yellow/red status badges | Task 9 |
| Scraper page pre-flight summary | Task 10 |
| `degraded` and `failed` plugins skipped | Task 8 (only healthy plugins passed to orchestrator) |
| Scrape result shows skipped plugins + duplicates discarded | Task 10 |
| DB schema fix (phone + social columns) | Task 1 |
