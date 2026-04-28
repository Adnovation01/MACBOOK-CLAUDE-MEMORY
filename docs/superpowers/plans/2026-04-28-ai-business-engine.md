# AI Business Engine — Unified Control Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a unified Flask + HTMX + Jinja2 web control panel integrating all modules of the ai_consulting_business project into one browser-based UI at localhost:5000.

**Architecture:** Extend existing `app.py` with Jinja2 template routes and new API endpoints. A shared `templates/base.html` provides the Clean Light sidebar shell. HTMX provides reactivity without a JS framework. All Python backend logic reuses existing `src/` modules unchanged (except one non-breaking addition to `ScraperOrchestrator`).

**Tech Stack:** Flask, Jinja2, HTMX (htmx.min.js ~45kb), python-dotenv, pandas + openpyxl (Excel export), SQLite (existing mission_control.db)

---

## File Map

**New files:**
- `templates/base.html` — shared sidebar/topbar shell (every page extends this)
- `templates/login.html` — login page
- `templates/dashboard.html` — section 4.1
- `templates/scraper.html` — section 4.2
- `templates/leads.html` — section 4.3
- `templates/outreach.html` — section 4.4
- `templates/content.html` — section 4.5
- `templates/plugins.html` — section 4.6
- `templates/settings.html` — section 4.7
- `static/style.css` — Clean Light CSS theme
- `static/htmx.min.js` — HTMX library (downloaded via curl)
- `tests/test_app_routes.py` — integration tests for all new routes
- `tests/test_settings_manager.py` — unit tests for .env save logic

**Modified files:**
- `app.py` — add template routes, scrape_state tracking, all new API endpoints
- `requirements.txt` — add flask-cors, openpyxl
- `src/scraper_orchestrator.py` — add optional `on_progress` callback to `scrape()` (non-breaking)

---

### Task 1: Foundation — routing skeleton, base template, CSS, HTMX, login

**Files:**
- Create: `templates/base.html`
- Create: `templates/login.html`
- Create: `static/style.css`
- Download: `static/htmx.min.js`
- Modify: `app.py`
- Modify: `requirements.txt`
- Create: `tests/test_app_routes.py`

- [ ] **Step 1: Update requirements.txt**

```
requests
beautifulsoup4
openai
pandas
python-dotenv
flask
flask-login
flask-cors
openpyxl
```

- [ ] **Step 2: Install new dependencies**

```bash
pip install flask-cors openpyxl
```

Expected: both packages install without error

- [ ] **Step 3: Download HTMX**

```bash
mkdir -p /Users/nalinpatel/ai_consulting_business/static
curl -L "https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js" -o /Users/nalinpatel/ai_consulting_business/static/htmx.min.js
```

Expected: `static/htmx.min.js` created (~45kb)

- [ ] **Step 4: Write failing tests**

Create `tests/test_app_routes.py`:

```python
import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app as flask_app

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c

def test_login_page_renders(client):
    resp = client.get('/login')
    assert resp.status_code == 200
    assert b'Login' in resp.data or b'login' in resp.data.lower()

def test_unauthenticated_dashboard_redirects(client):
    resp = client.get('/')
    assert resp.status_code in (302, 308)

def test_unauthenticated_scraper_redirects(client):
    resp = client.get('/scraper')
    assert resp.status_code in (302, 308)

def test_unauthenticated_leads_redirects(client):
    resp = client.get('/leads')
    assert resp.status_code in (302, 308)

def test_unauthenticated_settings_redirects(client):
    resp = client.get('/settings')
    assert resp.status_code in (302, 308)
```

- [ ] **Step 5: Run tests to verify they fail**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -m pytest tests/test_app_routes.py -v
```

Expected: FAIL — `/login` route does not exist yet

- [ ] **Step 6: Create templates/base.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block page_title %}Dashboard{% endblock %} — AI Engine</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
<div class="shell">
  <nav class="sidebar">
    <div class="sidebar-logo">
      ⚡ AI Engine
      <span class="badge-live">LIVE</span>
    </div>
    <div class="nav-label">Main</div>
    <a href="{{ url_for('dashboard') }}" class="nav-item {% if active == 'dashboard' %}active{% endif %}">
      <span>📊</span> Dashboard
    </a>
    <a href="{{ url_for('scraper') }}" class="nav-item {% if active == 'scraper' %}active{% endif %}">
      <span>🔍</span> Scraper
    </a>
    <a href="{{ url_for('leads') }}" class="nav-item {% if active == 'leads' %}active{% endif %}">
      <span>📋</span> Leads CRM
    </a>
    <div class="nav-label">Outreach</div>
    <a href="{{ url_for('outreach') }}" class="nav-item {% if active == 'outreach' %}active{% endif %}">
      <span>📧</span> Outreach
    </a>
    <a href="{{ url_for('content') }}" class="nav-item {% if active == 'content' %}active{% endif %}">
      <span>✍️</span> Content
    </a>
    <div class="nav-label">Config</div>
    <a href="{{ url_for('plugins') }}" class="nav-item {% if active == 'plugins' %}active{% endif %}">
      <span>🔌</span> Plugins
    </a>
    <a href="{{ url_for('settings') }}" class="nav-item {% if active == 'settings' %}active{% endif %}">
      <span>⚙️</span> Settings
    </a>
    <div class="sidebar-footer">
      {{ current_user.id }} &nbsp;·&nbsp;
      <a href="{{ url_for('logout') }}">Log out</a>
    </div>
  </nav>
  <div class="main">
    <div class="topbar">
      <h1>{% block heading %}{% endblock %}</h1>
      <div class="topbar-actions">{% block actions %}{% endblock %}</div>
    </div>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, msg in messages %}
        <div class="flash flash-{{ category }}">{{ msg }}</div>
      {% endfor %}
    {% endwith %}
    <div class="content">{% block content %}{% endblock %}</div>
  </div>
</div>
<script src="{{ url_for('static', filename='htmx.min.js') }}"></script>
{% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 7: Create templates/login.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Login — AI Engine</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body class="login-body">
  <div class="login-card">
    <div class="login-logo">⚡ AI Business Engine</div>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, msg in messages %}
        <div class="flash flash-{{ category }}" style="margin-bottom:12px;border-radius:6px;padding:8px 12px">{{ msg }}</div>
      {% endfor %}
    {% endwith %}
    <form method="POST" action="{{ url_for('login') }}">
      <div class="form-group">
        <label>Username</label>
        <input type="text" name="username" required autofocus>
      </div>
      <div class="form-group">
        <label>Password</label>
        <input type="password" name="password" required>
      </div>
      <button type="submit" class="btn btn-primary btn-full" style="margin-top:8px">Sign in</button>
    </form>
  </div>
</body>
</html>
```

- [ ] **Step 8: Create static/style.css**

```css
/* ===== RESET ===== */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f8fafc;color:#1e293b;font-size:14px}
a{text-decoration:none;color:inherit}

/* ===== SHELL ===== */
.shell{display:flex;height:100vh;overflow:hidden}

/* ===== SIDEBAR ===== */
.sidebar{width:220px;min-width:220px;background:white;border-right:1px solid #e2e8f0;display:flex;flex-direction:column}
.sidebar-logo{padding:18px 16px 14px;border-bottom:1px solid #f1f5f9;font-size:15px;font-weight:700;display:flex;align-items:center;gap:8px}
.badge-live{margin-left:auto;font-size:9px;background:#dcfce7;color:#15803d;padding:2px 7px;border-radius:20px;font-weight:600}
.nav-label{padding:12px 16px 4px;font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.07em;font-weight:600}
.nav-item{display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:6px;margin:1px 6px;font-size:13px;color:#475569;transition:background .1s}
.nav-item:hover{background:#f8fafc;color:#1e293b}
.nav-item.active{background:#eff6ff;color:#2563eb;font-weight:500}
.sidebar-footer{margin-top:auto;padding:12px 16px;border-top:1px solid #f1f5f9;font-size:11px;color:#94a3b8}
.sidebar-footer a{color:#94a3b8}
.sidebar-footer a:hover{color:#64748b}

/* ===== MAIN ===== */
.main{flex:1;display:flex;flex-direction:column;overflow:hidden}
.topbar{background:white;border-bottom:1px solid #e2e8f0;padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.topbar h1{font-size:16px;font-weight:600}
.topbar-actions{display:flex;gap:8px;align-items:center}
.content{flex:1;overflow-y:auto;padding:24px}

/* ===== FLASH ===== */
.flash{padding:10px 24px;font-size:13px}
.flash-success{background:#dcfce7;color:#15803d;border-bottom:1px solid #bbf7d0}
.flash-error{background:#fee2e2;color:#b91c1c;border-bottom:1px solid #fecaca}
.flash-info{background:#eff6ff;color:#1d4ed8;border-bottom:1px solid #bfdbfe}

/* ===== BUTTONS ===== */
.btn{padding:7px 14px;border-radius:7px;font-size:12px;font-weight:500;cursor:pointer;border:1px solid transparent;transition:all .15s;display:inline-flex;align-items:center;gap:5px}
.btn-primary{background:#2563eb;color:white;border-color:#2563eb}
.btn-primary:hover{background:#1d4ed8}
.btn-primary:disabled{background:#93c5fd;cursor:not-allowed}
.btn-secondary{background:#f8fafc;color:#475569;border-color:#e2e8f0}
.btn-secondary:hover{background:#f1f5f9}
.btn-secondary:disabled{opacity:.6;cursor:not-allowed}
.btn-success{background:#dcfce7;color:#15803d;border-color:#bbf7d0}
.btn-full{width:100%;justify-content:center;padding:10px}

/* ===== CARDS ===== */
.card{background:white;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;margin-bottom:16px}
.card-header{padding:14px 18px;border-bottom:1px solid #f1f5f9;display:flex;align-items:center;justify-content:space-between}
.card-header h3{font-size:13px;font-weight:600}
.card-body{padding:18px}

/* ===== STAT GRID ===== */
.stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}
.stat-card{background:white;border:1px solid #e2e8f0;border-radius:10px;padding:16px}
.stat-label{font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px}
.stat-value{font-size:28px;font-weight:700;color:#1e293b}
.stat-sub{font-size:11px;color:#94a3b8;margin-top:2px}
.stat-card.blue .stat-value{color:#2563eb}
.stat-card.green .stat-value{color:#059669}
.stat-card.orange .stat-value{color:#d97706}

/* ===== TABLES ===== */
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12px}
th{padding:9px 14px;text-align:left;font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;border-bottom:1px solid #f1f5f9;font-weight:600;white-space:nowrap}
td{padding:10px 14px;border-bottom:1px solid #f8fafc;color:#475569}
tr:last-child td{border-bottom:none}
tr:hover td{background:#fafafa}

/* ===== BADGES ===== */
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:500}
.badge-ready{background:#dcfce7;color:#15803d}
.badge-send{background:#dbeafe;color:#1d4ed8}
.badge-sent{background:#dbeafe;color:#1d4ed8}
.badge-skip{background:#f1f5f9;color:#64748b}
.badge-done{background:#f1f5f9;color:#64748b}
.badge-pending{background:#fef9c3;color:#a16207}
.badge-failed{background:#fee2e2;color:#b91c1c}
.badge-aida,.badge-bab,.badge-pas,.badge-spin,.badge-value_wedge,.badge-4ps,.badge-breakup{padding:2px 8px;border-radius:4px;font-size:10px;font-weight:500}
.badge-aida{background:#dbeafe;color:#1d4ed8}
.badge-bab{background:#fce7f3;color:#9d174d}
.badge-pas{background:#fef9c3;color:#a16207}
.badge-spin{background:#f0fdf4;color:#15803d}
.badge-value_wedge{background:#faf5ff;color:#7c3aed}
.badge-4ps{background:#fff7ed;color:#c2410c}
.badge-breakup{background:#f8fafc;color:#64748b}

/* ===== FORMS ===== */
.form-group{display:flex;flex-direction:column;gap:5px;margin-bottom:12px}
.form-group label{font-size:11px;font-weight:500;color:#374151}
.form-group input,.form-group select,.form-group textarea{padding:8px 11px;border:1px solid #e2e8f0;border-radius:7px;font-size:13px;color:#1e293b;background:white;outline:none;font-family:inherit}
.form-group input:focus,.form-group select:focus{border-color:#2563eb;box-shadow:0 0 0 3px #dbeafe}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.form-row-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}

/* ===== PROGRESS BAR ===== */
.progress-bar{background:#e2e8f0;border-radius:4px;height:8px;overflow:hidden}
.progress-fill{background:#2563eb;height:100%;border-radius:4px;transition:width .4s ease}

/* ===== PLUGIN TOGGLES ===== */
.plugin-section-label{font-size:10px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.07em;margin-bottom:10px;margin-top:20px}
.plugin-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:8px}
.plugin-card{background:white;border:1px solid #e2e8f0;border-radius:8px;padding:10px 12px;display:flex;align-items:center;justify-content:space-between;font-size:12px;color:#475569}
.plugin-card.enabled{border-color:#bfdbfe;background:#eff6ff;color:#1d4ed8}
.toggle-wrap{position:relative;display:inline-block;width:34px;height:20px;flex-shrink:0}
.toggle-wrap input{opacity:0;width:0;height:0}
.toggle-slider{position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background:#cbd5e1;border-radius:20px;transition:.2s}
.toggle-slider::before{content:'';position:absolute;height:14px;width:14px;left:3px;bottom:3px;background:white;border-radius:50%;transition:.2s;box-shadow:0 1px 2px rgba(0,0,0,.2)}
.toggle-wrap input:checked+.toggle-slider{background:#2563eb}
.toggle-wrap input:checked+.toggle-slider::before{transform:translateX(14px)}

/* ===== TABS ===== */
.tabs{display:flex;border-bottom:1px solid #e2e8f0;margin-bottom:18px}
.tab{padding:8px 16px;font-size:12px;color:#64748b;cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px}
.tab.active{color:#2563eb;border-bottom-color:#2563eb;font-weight:500}

/* ===== ALERTS ===== */
.alert{padding:10px 14px;border-radius:7px;font-size:12px;display:flex;align-items:center;gap:8px;margin-bottom:14px}
.alert-success{background:#dcfce7;color:#15803d;border:1px solid #bbf7d0}
.alert-error{background:#fee2e2;color:#b91c1c;border:1px solid #fecaca}
.alert-info{background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe}
.alert-warning{background:#fffbeb;color:#92400e;border:1px solid #fde68a}

/* ===== SEARCH BAR ===== */
.search-bar{padding:7px 12px;border:1px solid #e2e8f0;border-radius:7px;font-size:12px;width:220px;outline:none}
.search-bar:focus{border-color:#2563eb;box-shadow:0 0 0 3px #dbeafe}

/* ===== MODAL ===== */
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:100;align-items:center;justify-content:center}
.modal-overlay.open{display:flex}
.modal{background:white;border-radius:12px;padding:24px;max-width:560px;width:90%;max-height:80vh;overflow-y:auto}
.modal-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.modal-header h3{font-size:15px;font-weight:600}
.modal-close{background:none;border:none;font-size:18px;cursor:pointer;color:#94a3b8}

/* ===== ACTION SELECT ===== */
.action-select{font-size:11px;border:1px solid #e2e8f0;border-radius:4px;padding:3px 6px;color:#475569;background:white;cursor:pointer}

/* ===== LOGIN PAGE ===== */
.login-body{display:flex;align-items:center;justify-content:center;min-height:100vh;background:#f8fafc}
.login-card{background:white;border:1px solid #e2e8f0;border-radius:12px;padding:32px;width:360px}
.login-logo{font-size:18px;font-weight:700;margin-bottom:24px;color:#1e293b}
```

- [ ] **Step 9: Replace app.py with routing skeleton**

```python
from flask import (Flask, jsonify, request, render_template, redirect,
                   url_for, flash, send_file)
from flask_login import (LoginManager, UserMixin, login_user,
                         login_required, logout_user, current_user)
from flask_cors import CORS
import threading
import os
import json
import io
import smtplib
from dotenv import load_dotenv, dotenv_values
from src.database_manager import init_db, get_all_leads, update_lead_action

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-in-production-abc123')
CORS(app)
init_db()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'team.json')
ENV_PATH = os.path.join(os.path.dirname(__file__), '.env')

scrape_state = {
    'running': False, 'progress': 0,
    'leads_found': 0, 'current_plugin': '', 'error': None
}

PLUGIN_GROUPS = {
    'Search Engines': ['duckduckgo', 'google_search', 'bing_search', 'google_maps'],
    'Directories': ['yellowpages', 'yelp', 'bbb', 'manta', 'superpages',
                    'hotfrog', 'whitepages', 'foursquare', 'cylex', 'clutch', 'brownbook'],
    'Social (requires credentials)': ['facebook', 'instagram', 'linkedin',
                                       'twitter', 'youtube', 'reddit'],
    'Reviews & Niche': ['trustpilot', 'healthgrades', 'angi', 'thumbtack',
                        'opencorporates', 'state_registry'],
}

def load_team():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)['users']
    return {}

class User(UserMixin):
    def __init__(self, id): self.id = id

@login_manager.user_loader
def load_user(user_id):
    team = load_team()
    return User(user_id) if user_id in team else None

# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        team = load_team()
        if username in team and team[username]['password'] == password:
            login_user(User(username))
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    team = load_team()
    username = data.get('username', '')
    password = data.get('password', '')
    if username in team and team[username]['password'] == password:
        login_user(User(username))
        return jsonify({'status': 'success', 'role': team[username].get('role', 'member')})
    return jsonify({'status': 'error', 'message': 'Invalid credentials.'}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return jsonify({'status': 'success'})

# ── Page stubs (filled in later tasks) ───────────────────────────────────────

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html', active='dashboard',
        total_leads=0, emails_sent=0, queue_due=0, recent_leads=[])

@app.route('/scraper')
@login_required
def scraper():
    return render_template('scraper.html', active='scraper')

@app.route('/leads')
@login_required
def leads():
    return render_template('leads.html', active='leads', leads=[], niches=[], states=[])

@app.route('/outreach')
@login_required
def outreach():
    return render_template('outreach.html', active='outreach',
        has_gmail=False, pending=0, sent=0, failed=0)

@app.route('/content')
@login_required
def content():
    return render_template('content.html', active='content', posts=[])

@app.route('/plugins')
@login_required
def plugins():
    with open('config/scraper_config.json') as f:
        config = json.load(f)
    return render_template('plugins.html', active='plugins',
        plugin_groups=PLUGIN_GROUPS, config=config['plugins'])

@app.route('/settings')
@login_required
def settings():
    env = dotenv_values(ENV_PATH) if os.path.exists(ENV_PATH) else {}
    return render_template('settings.html', active='settings',
        email_user=env.get('EMAIL_USER', ''),
        email_pass_set=bool(env.get('EMAIL_PASS', '')),
        bcc_email=env.get('BCC_EMAIL', ''),
        your_name=env.get('YOUR_NAME', ''),
        your_title=env.get('YOUR_TITLE', ''),
        your_website=env.get('YOUR_WEBSITE', ''),
        openai_key_set=bool(env.get('OPENAI_API_KEY', '')),
        resend_key_set=bool(env.get('RESEND_API_KEY', '')),
        default_niche=env.get('DEFAULT_NICHE', ''),
        default_location=env.get('DEFAULT_LOCATION', ''))

# ── Existing API (unchanged) ──────────────────────────────────────────────────

@app.route('/api/leads', methods=['GET'])
@login_required
def get_leads():
    try:
        return jsonify({'status': 'success', 'data': get_all_leads()})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/update-lead', methods=['POST'])
@login_required
def update_lead():
    data = request.json or {}
    lead_id, new_action = data.get('lead_id'), data.get('action')
    if not lead_id or not new_action:
        return jsonify({'status': 'error', 'message': 'Missing data.'}), 400
    update_lead_action(lead_id, new_action)
    return jsonify({'status': 'success'})

@app.route('/api/scrape', methods=['POST'])
@login_required
def scrape():
    global scrape_state
    if scrape_state['running']:
        return jsonify({'status': 'error', 'message': 'Scrape already running'}), 409
    data = request.get_json() or {}
    keyword = data.get('keyword', 'dentist')
    location = data.get('location', 'nationwide')
    max_leads = int(data.get('max_leads', 50))

    def run():
        global scrape_state
        scrape_state = {'running': True, 'progress': 0, 'leads_found': 0,
                        'current_plugin': 'starting…', 'error': None}
        try:
            from src.plugins.plugin_factory import build_plugins
            from src.scraper_orchestrator import ScraperOrchestrator
            from src.email_sequence_manager import EmailSequenceManager

            def on_progress(plugin_name, leads_so_far):
                global scrape_state
                scrape_state['current_plugin'] = plugin_name
                scrape_state['leads_found'] = leads_so_far
                scrape_state['progress'] = min(
                    int((leads_so_far / max(max_leads, 1)) * 90), 90)

            plugins_list = build_plugins()
            orch = ScraperOrchestrator(plugins_list)
            results = orch.scrape(keyword, location, max_leads, on_progress=on_progress)

            scrape_state['progress'] = 95
            seq_mgr = EmailSequenceManager()
            os.makedirs('data', exist_ok=True)
            for lead in results:
                seq_mgr.schedule(lead)
            with open('data/leads.json', 'w') as f:
                json.dump([l.to_dict() for l in results], f, indent=2, default=str)
            scrape_state.update({
                'running': False, 'progress': 100,
                'leads_found': len(results), 'current_plugin': 'Done'})
        except Exception as e:
            scrape_state.update({'running': False, 'error': str(e)})

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'status': 'scrape started'})

@app.route('/api/scrape/status')
@login_required
def scrape_status():
    return jsonify(scrape_state)

# ── New API endpoints (filled in per-task) ────────────────────────────────────

@app.route('/api/leads/export')
@login_required
def export_leads():
    import pandas as pd
    leads_data = get_all_leads()
    if not leads_data:
        flash('No leads to export.', 'info')
        return redirect(url_for('leads'))
    df = pd.DataFrame(leads_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Leads')
    output.seek(0)
    return send_file(output, download_name='leads_export.xlsx', as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/api/outreach/queue')
@login_required
def outreach_queue():
    import sqlite3
    from src.database_manager import DB_PATH
    tab = request.args.get('tab', 'pending')
    status_map = {'pending': 'pending', 'sent': 'sent', 'failed': 'failed'}
    status = status_map.get(tab, 'pending')
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT * FROM email_sequences WHERE status=? ORDER BY scheduled_date ASC',
                (status,)).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify([])

@app.route('/api/outreach/send-due', methods=['POST'])
@login_required
def send_due():
    from src.email_sequence_manager import EmailSequenceManager
    from src.models.lead import Lead
    leads_path = 'data/leads.json'
    lead_lookup = {}
    if os.path.exists(leads_path):
        with open(leads_path) as f:
            raw = json.load(f)
        valid_fields = Lead.__dataclass_fields__.keys()
        for item in raw:
            if item.get('email'):
                lead_lookup[item['email']] = Lead(
                    **{k: v for k, v in item.items() if k in valid_fields})
    try:
        EmailSequenceManager().send_due(lead_lookup)
        return jsonify({'status': 'success', 'message': 'Due emails sent.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/outreach/unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    email = (request.json or {}).get('email', '')
    if not email:
        return jsonify({'status': 'error', 'message': 'Missing email'}), 400
    from src.email_sequence_manager import EmailSequenceManager
    EmailSequenceManager().mark_unsubscribed(email)
    return jsonify({'status': 'success'})

@app.route('/api/content/generate', methods=['POST'])
@login_required
def generate_content():
    from src.content_generator import generate_social_content
    try:
        generate_social_content()
        content_path = 'data/marketing_content.json'
        posts = json.load(open(content_path)) if os.path.exists(content_path) else []
        return jsonify({'status': 'success', 'posts': posts})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/plugins/toggle', methods=['POST'])
@login_required
def toggle_plugin():
    data = request.json or {}
    plugin_name = data.get('plugin')
    enabled = data.get('enabled', False)
    config_path = 'config/scraper_config.json'
    with open(config_path) as f:
        config = json.load(f)
    if plugin_name not in config['plugins']:
        return jsonify({'status': 'error', 'message': 'Unknown plugin'}), 400
    config['plugins'][plugin_name]['enabled'] = bool(enabled)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    return jsonify({'status': 'success', 'plugin': plugin_name, 'enabled': enabled})

def _save_env(updates: dict):
    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            lines = f.readlines()
    existing = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            existing[key] = i
    for key, value in updates.items():
        if key in existing:
            lines[existing[key]] = f'{key}={value}\n'
        else:
            lines.append(f'{key}={value}\n')
    with open(ENV_PATH, 'w') as f:
        f.writelines(lines)
    load_dotenv(ENV_PATH, override=True)

@app.route('/api/settings/save', methods=['POST'])
@login_required
def save_settings():
    data = request.json or {}
    field_map = {
        'email_user': 'EMAIL_USER', 'email_pass': 'EMAIL_PASS',
        'bcc_email': 'BCC_EMAIL', 'your_name': 'YOUR_NAME',
        'your_title': 'YOUR_TITLE', 'your_website': 'YOUR_WEBSITE',
        'openai_key': 'OPENAI_API_KEY', 'resend_key': 'RESEND_API_KEY',
        'default_niche': 'DEFAULT_NICHE', 'default_location': 'DEFAULT_LOCATION',
    }
    updates = {}
    for form_key, env_key in field_map.items():
        val = data.get(form_key, '').strip()
        if val and val != '••••••••':
            updates[env_key] = val
    _save_env(updates)
    return jsonify({'status': 'success', 'message': 'Settings saved.'})

@app.route('/api/settings/test-gmail', methods=['POST'])
@login_required
def test_gmail():
    data = request.json or {}
    user = data.get('email_user', os.environ.get('EMAIL_USER', ''))
    password = data.get('email_pass', os.environ.get('EMAIL_PASS', ''))
    if not user or not password or password == '••••••••':
        return jsonify({'status': 'error',
                        'message': 'Enter Gmail address and App Password first.'})
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(user, password)
        return jsonify({'status': 'success', 'message': '✅ Gmail connection successful!'})
    except smtplib.SMTPAuthenticationError:
        return jsonify({'status': 'error',
                        'message': 'Authentication failed — use an App Password, not your account password.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

- [ ] **Step 10: Create stub templates so all routes render without error**

```bash
mkdir -p /Users/nalinpatel/ai_consulting_business/templates
```

Create each file with the minimum content below.

`templates/dashboard.html`:
```html
{% extends "base.html" %}
{% block page_title %}Dashboard{% endblock %}
{% block heading %}Dashboard{% endblock %}
{% block content %}<p style="color:#94a3b8">Dashboard — coming in Task 2.</p>{% endblock %}
```

`templates/scraper.html`:
```html
{% extends "base.html" %}
{% block page_title %}Scraper{% endblock %}
{% block heading %}Scraper{% endblock %}
{% block content %}<p style="color:#94a3b8">Scraper — coming in Task 3.</p>{% endblock %}
```

`templates/leads.html`:
```html
{% extends "base.html" %}
{% block page_title %}Leads CRM{% endblock %}
{% block heading %}Leads CRM{% endblock %}
{% block content %}<p style="color:#94a3b8">Leads — coming in Task 4.</p>{% endblock %}
```

`templates/outreach.html`:
```html
{% extends "base.html" %}
{% block page_title %}Outreach{% endblock %}
{% block heading %}Outreach{% endblock %}
{% block content %}<p style="color:#94a3b8">Outreach — coming in Task 5.</p>{% endblock %}
```

`templates/content.html`:
```html
{% extends "base.html" %}
{% block page_title %}Content{% endblock %}
{% block heading %}Content Generator{% endblock %}
{% block content %}<p style="color:#94a3b8">Content — coming in Task 6.</p>{% endblock %}
```

`templates/plugins.html`:
```html
{% extends "base.html" %}
{% block page_title %}Plugins{% endblock %}
{% block heading %}Plugins{% endblock %}
{% block content %}<p style="color:#94a3b8">Plugins — coming in Task 7.</p>{% endblock %}
```

`templates/settings.html`:
```html
{% extends "base.html" %}
{% block page_title %}Settings{% endblock %}
{% block heading %}Settings & Credentials{% endblock %}
{% block content %}<p style="color:#94a3b8">Settings — coming in Task 8.</p>{% endblock %}
```

- [ ] **Step 11: Run tests — should all pass now**

```bash
cd /Users/nalinpatel/ai_consulting_business && python -m pytest tests/test_app_routes.py -v
```

Expected: All 5 tests PASS

- [ ] **Step 12: Commit**

```bash
cd /Users/nalinpatel/ai_consulting_business
git add templates/ static/ requirements.txt app.py tests/test_app_routes.py
git commit -m "feat: add foundation — base template, Clean Light CSS, routing skeleton, login page

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 2: Dashboard Page

**Files:**
- Modify: `templates/dashboard.html`
- Modify: `app.py` — update `dashboard()` route with real stats

- [ ] **Step 1: Update dashboard() route in app.py**

Replace the stub `dashboard()` function:

```python
@app.route('/')
@login_required
def dashboard():
    import sqlite3
    from src.database_manager import DB_PATH
    from datetime import datetime
    all_leads = get_all_leads()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            now = datetime.utcnow().isoformat()
            queue_due = conn.execute(
                "SELECT COUNT(*) FROM email_sequences WHERE status='pending' AND scheduled_date<=?",
                (now,)).fetchone()[0]
            emails_sent = conn.execute(
                "SELECT COUNT(*) FROM email_sequences WHERE status='sent'"
            ).fetchone()[0]
    except Exception:
        queue_due = 0
        emails_sent = 0
    return render_template('dashboard.html', active='dashboard',
        total_leads=len(all_leads),
        emails_sent=emails_sent,
        queue_due=queue_due,
        recent_leads=all_leads[:10])
```

- [ ] **Step 2: Build templates/dashboard.html**

```html
{% extends "base.html" %}
{% block page_title %}Dashboard{% endblock %}
{% block heading %}Dashboard{% endblock %}
{% block actions %}
  <a href="{{ url_for('export_leads') }}" class="btn btn-secondary">📥 Export Excel</a>
  <a href="{{ url_for('scraper') }}" class="btn btn-primary">▶ New Campaign</a>
{% endblock %}

{% block content %}
<div class="stat-grid">
  <div class="stat-card">
    <div class="stat-label">Total Leads</div>
    <div class="stat-value">{{ total_leads }}</div>
    <div class="stat-sub">in database</div>
  </div>
  <div class="stat-card blue">
    <div class="stat-label">Emails Sent</div>
    <div class="stat-value">{{ emails_sent }}</div>
    <div class="stat-sub">via sequences</div>
  </div>
  <div class="stat-card orange">
    <div class="stat-label">Due Today</div>
    <div class="stat-value">{{ queue_due }}</div>
    <div class="stat-sub">emails in queue</div>
  </div>
  <div class="stat-card green">
    <div class="stat-label">Engine</div>
    <div class="stat-value" style="font-size:18px">Ready</div>
    <div class="stat-sub"><a href="{{ url_for('scraper') }}" style="color:#059669">run a campaign →</a></div>
  </div>
</div>

<div class="card">
  <div class="card-header">
    <h3>Recent Leads</h3>
    <a href="{{ url_for('leads') }}" class="btn btn-secondary" style="font-size:11px;padding:5px 10px">View all →</a>
  </div>
  {% if recent_leads %}
  <div class="table-wrap">
    <table>
      <thead>
        <tr><th>Business</th><th>Email</th><th>Location</th><th>Niche</th><th>Status</th></tr>
      </thead>
      <tbody>
        {% for lead in recent_leads %}
        <tr>
          <td><strong>{{ lead.name or '—' }}</strong></td>
          <td style="font-size:11px">{{ lead.email or '—' }}</td>
          <td>{{ lead.location or '—' }}</td>
          <td>{{ lead.niche or '—' }}</td>
          <td><span class="badge badge-{{ (lead.action or 'ready') | lower }}">{{ lead.action or 'READY' }}</span></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="card-body" style="text-align:center;color:#94a3b8;padding:40px">
    No leads yet. <a href="{{ url_for('scraper') }}" style="color:#2563eb">Run a scraping campaign →</a>
  </div>
  {% endif %}
</div>
{% endblock %}
```

- [ ] **Step 3: Run app and verify**

```bash
python app.py
```

Open http://localhost:5000 → login with `admin` / `team_password_123` → dashboard shows stat cards and recent leads table.

- [ ] **Step 4: Commit**

```bash
git add templates/dashboard.html app.py
git commit -m "feat: implement dashboard page with live stats and recent leads table

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 3: Scraper Page with Live Progress

**Files:**
- Modify: `src/scraper_orchestrator.py` — add `on_progress` callback
- Modify: `templates/scraper.html`

- [ ] **Step 1: Write failing test for on_progress callback**

Add to `tests/test_app_routes.py`:

```python
def test_scrape_status_endpoint_returns_json(client):
    with patch('app.load_team', return_value={'admin': {'password': 'pass', 'role': 'admin'}}):
        client.post('/login', data={'username': 'admin', 'password': 'pass'})
        resp = client.get('/api/scrape/status')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'running' in data
        assert 'progress' in data
        assert 'leads_found' in data

def test_orchestrator_accepts_on_progress_callback():
    from src.scraper_orchestrator import ScraperOrchestrator
    import inspect
    sig = inspect.signature(ScraperOrchestrator.scrape)
    assert 'on_progress' in sig.parameters
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_app_routes.py::test_orchestrator_accepts_on_progress_callback -v
```

Expected: FAIL — `on_progress` not in signature yet

- [ ] **Step 3: Add on_progress to src/scraper_orchestrator.py**

In `src/scraper_orchestrator.py`, update only the `scrape` method signature and the `as_completed` loop body:

```python
def scrape(self, keyword: str, location: str, max_leads: int = 50, on_progress=None) -> List[Lead]:
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

    merged = self._deduplicator.deduplicate(all_leads)
    enriched = [self._enricher.enrich(lead) for lead in merged]
    return self._score(enriched)[:max_leads]
```

- [ ] **Step 4: Run existing orchestrator tests to check no regression**

```bash
python -m pytest tests/test_orchestrator.py -v
```

Expected: All PASS

- [ ] **Step 5: Run new tests**

```bash
python -m pytest tests/test_app_routes.py -v
```

Expected: All PASS including the two new ones

- [ ] **Step 6: Build templates/scraper.html**

```html
{% extends "base.html" %}
{% block page_title %}Scraper{% endblock %}
{% block heading %}Scraper{% endblock %}

{% block content %}
<div class="card">
  <div class="card-header"><h3>New Campaign</h3></div>
  <div class="card-body">
    <form id="scrape-form">
      <div class="form-row-3">
        <div class="form-group">
          <label>Industry / Niche</label>
          <input type="text" name="keyword" value="Dentist" placeholder="e.g. Dentist, Roofing, Yoga…" required>
        </div>
        <div class="form-group">
          <label>Location</label>
          <input type="text" name="location" value="California" placeholder="City, State or 'nationwide'" required>
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
      <button type="submit" class="btn btn-primary" id="run-btn">▶ Run Campaign</button>
    </form>
  </div>
</div>

<div class="card" id="progress-card" style="display:none">
  <div class="card-header">
    <h3>Live Progress</h3>
    <span id="status-text" style="font-size:12px;color:#64748b">Starting…</span>
  </div>
  <div class="card-body">
    <div style="display:flex;justify-content:space-between;margin-bottom:6px;font-size:12px;color:#475569">
      <span id="plugin-label">Initialising plugins…</span>
      <span id="lead-count">0 leads found</span>
    </div>
    <div class="progress-bar">
      <div class="progress-fill" id="progress-fill" style="width:0%"></div>
    </div>
  </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.getElementById('scrape-form').addEventListener('submit', async function(e) {
  e.preventDefault();
  const btn = document.getElementById('run-btn');
  btn.disabled = true;
  btn.textContent = '⏳ Running…';
  document.getElementById('progress-card').style.display = 'block';
  document.getElementById('status-text').textContent = 'Starting…';
  document.getElementById('status-text').style.color = '#64748b';

  await fetch('/api/scrape', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      keyword: this.keyword.value,
      location: this.location.value,
      max_leads: parseInt(this.max_leads.value)
    })
  });

  const poll = setInterval(async () => {
    const r = await fetch('/api/scrape/status');
    const s = await r.json();
    document.getElementById('progress-fill').style.width = s.progress + '%';
    document.getElementById('lead-count').textContent = s.leads_found + ' leads found';
    document.getElementById('plugin-label').textContent = s.current_plugin || 'Running…';
    if (!s.running && s.progress > 0) {
      clearInterval(poll);
      btn.disabled = false;
      btn.textContent = '▶ Run Campaign';
      if (s.error) {
        document.getElementById('status-text').textContent = '❌ Error: ' + s.error;
        document.getElementById('status-text').style.color = '#b91c1c';
      } else {
        document.getElementById('status-text').textContent = '✅ Done — ' + s.leads_found + ' leads saved';
        document.getElementById('status-text').style.color = '#15803d';
      }
    }
  }, 2000);
});
</script>
{% endblock %}
```

- [ ] **Step 7: Commit**

```bash
git add templates/scraper.html src/scraper_orchestrator.py app.py tests/test_app_routes.py
git commit -m "feat: implement scraper page with live 2s-polling progress bar

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 4: Leads CRM + Excel Export

**Files:**
- Modify: `templates/leads.html`
- Modify: `app.py` — update `leads()` route with real data

- [ ] **Step 1: Add test for export endpoint**

Add to `tests/test_app_routes.py`:

```python
def test_export_leads_requires_auth(client):
    resp = client.get('/api/leads/export')
    assert resp.status_code in (302, 308)
```

- [ ] **Step 2: Update leads() route in app.py**

Replace stub:

```python
@app.route('/leads')
@login_required
def leads():
    all_leads = get_all_leads()
    niches = sorted(set(l.get('niche', '') for l in all_leads if l.get('niche')))
    return render_template('leads.html', active='leads',
        leads=all_leads, niches=niches)
```

- [ ] **Step 3: Build templates/leads.html**

```html
{% extends "base.html" %}
{% block page_title %}Leads CRM{% endblock %}
{% block heading %}Leads CRM <span style="font-size:13px;font-weight:400;color:#94a3b8;margin-left:8px">{{ leads|length }} total</span>{% endblock %}
{% block actions %}
  <input class="search-bar" type="text" id="lead-search" placeholder="🔍 Search leads…" oninput="filterLeads()">
  <a href="{{ url_for('export_leads') }}" class="btn btn-success">📥 Export Excel</a>
{% endblock %}

{% block content %}
{% if leads %}
<div class="card">
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Business</th><th>Email</th><th>Location</th>
          <th>Niche</th><th>Pain Points</th><th>Action</th>
        </tr>
      </thead>
      <tbody id="leads-body">
        {% for lead in leads %}
        <tr class="lead-row">
          <td><strong>{{ lead.name or '—' }}</strong></td>
          <td style="font-size:11px">{{ lead.email or '—' }}</td>
          <td>{{ lead.location or '—' }}</td>
          <td>{{ lead.niche or '—' }}</td>
          <td style="font-size:11px;color:#64748b;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="{{ lead.pain_points or '' }}">
            {{ lead.pain_points or '—' }}
          </td>
          <td>
            <select class="action-select" id="sel-{{ lead.id }}"
              onchange="updateAction({{ lead.id }}, this.value)">
              {% for opt in ['READY','SEND','SKIP','DONE'] %}
                <option value="{{ opt }}" {% if lead.action == opt %}selected{% endif %}>{{ opt }}</option>
              {% endfor %}
            </select>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% else %}
<div class="card">
  <div class="card-body" style="text-align:center;color:#94a3b8;padding:48px">
    No leads yet. <a href="{{ url_for('scraper') }}" style="color:#2563eb">Run a scraping campaign →</a>
  </div>
</div>
{% endif %}
{% endblock %}

{% block scripts %}
<script>
function filterLeads() {
  const q = document.getElementById('lead-search').value.toLowerCase();
  document.querySelectorAll('.lead-row').forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

async function updateAction(leadId, action) {
  const r = await fetch('/api/update-lead', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({lead_id: leadId, action: action})
  });
  const data = await r.json();
  if (data.status !== 'success') {
    alert('Failed to update: ' + (data.message || 'unknown error'));
  }
}
</script>
{% endblock %}
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_app_routes.py -v
```

Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add templates/leads.html app.py tests/test_app_routes.py
git commit -m "feat: implement leads CRM with client-side search, action update, and Excel export

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 5: Outreach Page

**Files:**
- Modify: `templates/outreach.html`
- Modify: `app.py` — update `outreach()` route with real counts

- [ ] **Step 1: Update outreach() route in app.py**

Replace stub:

```python
@app.route('/outreach')
@login_required
def outreach():
    import sqlite3
    from src.database_manager import DB_PATH
    from datetime import datetime
    has_gmail = bool(os.environ.get('EMAIL_USER')) and bool(os.environ.get('EMAIL_PASS'))
    try:
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(DB_PATH) as conn:
            pending = conn.execute(
                "SELECT COUNT(*) FROM email_sequences WHERE status='pending' AND scheduled_date<=?",
                (now,)).fetchone()[0]
            sent = conn.execute(
                "SELECT COUNT(*) FROM email_sequences WHERE status='sent'"
            ).fetchone()[0]
            failed = conn.execute(
                "SELECT COUNT(*) FROM email_sequences WHERE status='failed'"
            ).fetchone()[0]
    except Exception:
        pending = sent = failed = 0
    return render_template('outreach.html', active='outreach',
        has_gmail=has_gmail, pending=pending, sent=sent, failed=failed)
```

- [ ] **Step 2: Build templates/outreach.html**

```html
{% extends "base.html" %}
{% block page_title %}Outreach{% endblock %}
{% block heading %}Outreach{% endblock %}
{% block actions %}
  <button class="btn btn-primary" id="send-btn" onclick="sendDue()">
    ▶ Send Due Emails ({{ pending }})
  </button>
{% endblock %}

{% block content %}
{% if not has_gmail %}
<div class="alert alert-warning">
  ⚠️ Gmail not configured.
  <a href="{{ url_for('settings') }}" style="color:#92400e;font-weight:500">Add credentials in Settings →</a>
</div>
{% endif %}

<div id="send-result"></div>

<div class="tabs">
  <div class="tab active" onclick="loadTab('pending', this)">Queue ({{ pending }})</div>
  <div class="tab" onclick="loadTab('sent', this)">Sent ({{ sent }})</div>
  <div class="tab" onclick="loadTab('failed', this)">Failed ({{ failed }})</div>
</div>

<div class="card">
  <div class="table-wrap">
    <table>
      <thead>
        <tr><th>Business</th><th>Email</th><th>Framework</th><th>Scheduled</th><th></th></tr>
      </thead>
      <tbody id="queue-body">
        <tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:24px">Loading…</td></tr>
      </tbody>
    </table>
  </div>
</div>
{% endblock %}

{% block scripts %}
<script>
const FW = {aida:'AIDA',bab:'BAB',pas:'PAS',spin:'SPIN',value_wedge:'Value Wedge','4ps':'4Ps',breakup:'Breakup'};

async function loadTab(tab, el) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  if (el) el.classList.add('active');
  const r = await fetch('/api/outreach/queue?tab=' + tab);
  const rows = await r.json();
  const body = document.getElementById('queue-body');
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:24px">No emails in this tab.</td></tr>';
    return;
  }
  body.innerHTML = rows.map(row => `
    <tr>
      <td><strong>${row.business_name || '—'}</strong></td>
      <td style="font-size:11px">${row.lead_email}</td>
      <td><span class="badge badge-${row.framework}">${FW[row.framework] || row.framework}</span></td>
      <td style="font-size:11px">${(row.scheduled_date || '').split('T')[0]}</td>
      <td>
        <button class="btn btn-secondary" style="font-size:10px;padding:3px 8px"
          onclick="unsub('${row.lead_email}')">Unsub</button>
      </td>
    </tr>
  `).join('');
}

async function sendDue() {
  const btn = document.getElementById('send-btn');
  btn.disabled = true; btn.textContent = '⏳ Sending…';
  const r = await fetch('/api/outreach/send-due', {method: 'POST'});
  const data = await r.json();
  btn.disabled = false; btn.textContent = '▶ Send Due Emails';
  const div = document.getElementById('send-result');
  div.innerHTML = data.status === 'success'
    ? `<div class="alert alert-success">✅ ${data.message}</div>`
    : `<div class="alert alert-error">❌ ${data.message}</div>`;
  loadTab('pending', document.querySelector('.tab'));
}

async function unsub(email) {
  if (!confirm('Unsubscribe ' + email + ' from all pending sequences?')) return;
  await fetch('/api/outreach/unsubscribe', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({email})
  });
  loadTab('pending', document.querySelector('.tab.active'));
}

document.addEventListener('DOMContentLoaded', () =>
  loadTab('pending', document.querySelector('.tab')));
</script>
{% endblock %}
```

- [ ] **Step 3: Commit**

```bash
git add templates/outreach.html app.py
git commit -m "feat: implement outreach page with queue tabs, send-due, and unsubscribe

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 6: Content Page

**Files:**
- Modify: `templates/content.html`
- Modify: `app.py` — update `content()` route with stored posts

- [ ] **Step 1: Update content() route in app.py**

Replace stub:

```python
@app.route('/content')
@login_required
def content():
    posts = []
    content_path = 'data/marketing_content.json'
    if os.path.exists(content_path):
        with open(content_path) as f:
            posts = json.load(f)
    return render_template('content.html', active='content', posts=posts)
```

- [ ] **Step 2: Build templates/content.html**

```html
{% extends "base.html" %}
{% block page_title %}Content{% endblock %}
{% block heading %}Content Generator{% endblock %}
{% block actions %}
  <button class="btn btn-primary" onclick="generatePosts(this)">✨ Generate Posts</button>
{% endblock %}

{% block content %}
<div id="gen-result"></div>
<div id="posts-wrap">
{% if posts %}
  {% for post in posts %}
  <div class="card">
    <div class="card-header">
      <h3>{{ post.title }}</h3>
      <button class="btn btn-secondary" style="font-size:11px"
        onclick="copyPost(this, {{ loop.index0 }})">📋 Copy</button>
    </div>
    <div class="card-body" style="white-space:pre-wrap;font-size:13px;color:#475569;line-height:1.6"
      id="post-{{ loop.index0 }}">{{ post.content }}</div>
  </div>
  {% endfor %}
{% else %}
  <div class="card">
    <div class="card-body" style="text-align:center;color:#94a3b8;padding:48px">
      No posts yet. Click <strong>✨ Generate Posts</strong> to create LinkedIn content from your recent leads.
    </div>
  </div>
{% endif %}
</div>
{% endblock %}

{% block scripts %}
<script>
async function generatePosts(btn) {
  btn.disabled = true; btn.textContent = '⏳ Generating…';
  const r = await fetch('/api/content/generate', {method: 'POST'});
  const data = await r.json();
  btn.disabled = false; btn.textContent = '✨ Generate Posts';
  if (data.status === 'success') {
    document.getElementById('posts-wrap').innerHTML = data.posts.map((p, i) => `
      <div class="card">
        <div class="card-header">
          <h3>${p.title}</h3>
          <button class="btn btn-secondary" style="font-size:11px"
            onclick="copyPost(this, ${i})">📋 Copy</button>
        </div>
        <div class="card-body" style="white-space:pre-wrap;font-size:13px;color:#475569;line-height:1.6"
          id="post-${i}">${p.content}</div>
      </div>
    `).join('');
  } else {
    document.getElementById('gen-result').innerHTML =
      `<div class="alert alert-error">❌ ${data.message}</div>`;
  }
}

function copyPost(btn, idx) {
  const text = document.getElementById('post-' + idx).textContent;
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = '✅ Copied';
    setTimeout(() => { btn.textContent = '📋 Copy'; }, 2000);
  });
}
</script>
{% endblock %}
```

- [ ] **Step 3: Commit**

```bash
git add templates/content.html app.py
git commit -m "feat: implement content generator page with copy-to-clipboard

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 7: Plugins Page

**Files:**
- Modify: `templates/plugins.html`

The route and API are already complete in `app.py` from Task 1.

- [ ] **Step 1: Build templates/plugins.html**

```html
{% extends "base.html" %}
{% block page_title %}Plugins{% endblock %}
{% block heading %}Plugins{% endblock %}
{% block actions %}
  <span id="save-status" style="font-size:12px;color:#15803d"></span>
{% endblock %}

{% block content %}
{% for group_name, plugin_names in plugin_groups.items() %}
<div class="plugin-section-label">{{ group_name }}</div>
<div class="plugin-grid">
  {% for pname in plugin_names %}
  {% set enabled = config.get(pname, {}).get('enabled', false) %}
  <div class="plugin-card {% if enabled %}enabled{% endif %}" id="card-{{ pname }}">
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
  💡 Social plugins (Facebook, Instagram, LinkedIn, Twitter) require account credentials.
  Add session cookies in <a href="{{ url_for('settings') }}" style="color:#1d4ed8">Settings →</a>
</div>
{% endblock %}

{% block scripts %}
<script>
async function togglePlugin(name, enabled, checkbox) {
  const r = await fetch('/api/plugins/toggle', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({plugin: name, enabled: enabled})
  });
  const data = await r.json();
  const card = document.getElementById('card-' + name);
  if (data.status === 'success') {
    card.classList.toggle('enabled', enabled);
    const msg = document.getElementById('save-status');
    msg.textContent = '✅ Saved';
    setTimeout(() => { msg.textContent = ''; }, 2000);
  } else {
    checkbox.checked = !enabled;
    alert('Failed: ' + data.message);
  }
}
</script>
{% endblock %}
```

- [ ] **Step 2: Commit**

```bash
git add templates/plugins.html
git commit -m "feat: implement plugins page with live toggle persistence

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 8: Settings & Credentials Page

**Files:**
- Modify: `templates/settings.html`
- Create: `tests/test_settings_manager.py`

The routes are complete in `app.py` from Task 1.

- [ ] **Step 1: Write unit tests for _save_env logic**

Create `tests/test_settings_manager.py`:

```python
import os
import pytest
import tempfile

def save_env_logic(updates: dict, env_path: str):
    """Copy of _save_env from app.py — tests the algorithm in isolation."""
    lines = []
    if os.path.exists(env_path):
        with open(env_path) as f:
            lines = f.readlines()
    existing = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            existing[key] = i
    for key, value in updates.items():
        if key in existing:
            lines[existing[key]] = f'{key}={value}\n'
        else:
            lines.append(f'{key}={value}\n')
    with open(env_path, 'w') as f:
        f.writelines(lines)

def test_creates_new_key():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write('EXISTING=old\n')
        path = f.name
    try:
        save_env_logic({'NEW_KEY': 'new_value'}, path)
        content = open(path).read()
        assert 'NEW_KEY=new_value' in content
        assert 'EXISTING=old' in content
    finally:
        os.unlink(path)

def test_updates_existing_key():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write('EMAIL_USER=old@gmail.com\n')
        path = f.name
    try:
        save_env_logic({'EMAIL_USER': 'new@gmail.com'}, path)
        content = open(path).read()
        assert 'EMAIL_USER=new@gmail.com' in content
        assert 'old@gmail.com' not in content
    finally:
        os.unlink(path)

def test_handles_missing_file():
    path = '/tmp/test_missing_env_xyz123.env'
    if os.path.exists(path): os.unlink(path)
    save_env_logic({'KEY': 'val'}, path)
    assert os.path.exists(path)
    assert 'KEY=val' in open(path).read()
    os.unlink(path)

def test_preserves_comments():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write('# Gmail config\nEMAIL_USER=x@gmail.com\n')
        path = f.name
    try:
        save_env_logic({'EMAIL_USER': 'y@gmail.com'}, path)
        content = open(path).read()
        assert '# Gmail config' in content
        assert 'EMAIL_USER=y@gmail.com' in content
    finally:
        os.unlink(path)
```

- [ ] **Step 2: Run tests**

```bash
python -m pytest tests/test_settings_manager.py -v
```

Expected: All 4 PASS

- [ ] **Step 3: Build templates/settings.html**

```html
{% extends "base.html" %}
{% block page_title %}Settings{% endblock %}
{% block heading %}Settings & Credentials{% endblock %}
{% block actions %}
  <span id="save-msg" style="font-size:12px;color:#15803d"></span>
  <button class="btn btn-primary" onclick="saveAll(this)">💾 Save All</button>
{% endblock %}

{% block content %}
<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">

  <div class="card">
    <div class="card-header"><h3>📧 Gmail Outreach</h3></div>
    <div class="card-body">
      <div class="form-row">
        <div class="form-group">
          <label>Gmail Address</label>
          <input type="email" id="email_user" value="{{ email_user }}" placeholder="you@gmail.com">
        </div>
        <div class="form-group">
          <label>App Password</label>
          <input type="password" id="email_pass"
            placeholder="{{ '••••••••' if email_pass_set else 'xxxx xxxx xxxx xxxx' }}">
        </div>
      </div>
      <div class="form-group">
        <label>BCC Email (optional)</label>
        <input type="email" id="bcc_email" value="{{ bcc_email }}" placeholder="bcc@yourdomain.com">
      </div>
      <button class="btn btn-secondary" onclick="testGmail(this)" style="margin-top:4px">
        ✅ Test Connection
      </button>
      <div id="gmail-result" style="margin-top:8px;font-size:12px"></div>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><h3>🔑 API Keys</h3></div>
    <div class="card-body">
      <div class="form-group">
        <label>OpenAI API Key</label>
        <input type="password" id="openai_key"
          placeholder="{{ '••••••••' if openai_key_set else 'sk-…' }}">
      </div>
      <div class="form-group">
        <label>Resend API Key</label>
        <input type="password" id="resend_key"
          placeholder="{{ '••••••••' if resend_key_set else 're_…' }}">
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <h3>👤 Your Identity</h3>
      <span style="font-size:11px;color:#94a3b8">Also used as email sender name</span>
    </div>
    <div class="card-body">
      <div class="form-row">
        <div class="form-group">
          <label>Your Name</label>
          <input type="text" id="your_name" value="{{ your_name }}" placeholder="Nalin Patel">
        </div>
        <div class="form-group">
          <label>Your Title</label>
          <input type="text" id="your_title" value="{{ your_title }}" placeholder="AI Consultant">
        </div>
      </div>
      <div class="form-group">
        <label>Your Website</label>
        <input type="text" id="your_website" value="{{ your_website }}" placeholder="https://yourdomain.com">
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><h3>🎯 Campaign Defaults</h3></div>
    <div class="card-body">
      <div class="form-row">
        <div class="form-group">
          <label>Default Niche</label>
          <input type="text" id="default_niche" value="{{ default_niche }}" placeholder="Dentist">
        </div>
        <div class="form-group">
          <label>Default Location</label>
          <input type="text" id="default_location" value="{{ default_location }}" placeholder="California">
        </div>
      </div>
    </div>
  </div>

</div>

<div class="alert alert-info" style="margin-top:4px">
  💾 Saved to your local <code>.env</code> file — never leaves your machine.
  Make sure <code>.env</code> is in your <code>.gitignore</code>.
</div>
{% endblock %}

{% block scripts %}
<script>
function fv(id) { return document.getElementById(id).value.trim(); }

async function saveAll(btn) {
  btn.disabled = true; btn.textContent = '⏳ Saving…';
  const r = await fetch('/api/settings/save', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      email_user: fv('email_user'), email_pass: fv('email_pass'),
      bcc_email: fv('bcc_email'), your_name: fv('your_name'),
      your_title: fv('your_title'), your_website: fv('your_website'),
      openai_key: fv('openai_key'), resend_key: fv('resend_key'),
      default_niche: fv('default_niche'), default_location: fv('default_location'),
    })
  });
  const data = await r.json();
  btn.disabled = false; btn.textContent = '💾 Save All';
  const msg = document.getElementById('save-msg');
  msg.textContent = data.status === 'success' ? '✅ Saved' : '❌ ' + data.message;
  setTimeout(() => { msg.textContent = ''; }, 3000);
}

async function testGmail(btn) {
  btn.disabled = true; btn.textContent = '⏳ Testing…';
  const r = await fetch('/api/settings/test-gmail', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email_user: fv('email_user'), email_pass: fv('email_pass')})
  });
  const data = await r.json();
  btn.disabled = false; btn.textContent = '✅ Test Connection';
  const el = document.getElementById('gmail-result');
  el.textContent = data.message;
  el.style.color = data.status === 'success' ? '#15803d' : '#b91c1c';
}
</script>
{% endblock %}
```

- [ ] **Step 4: Run full test suite**

```bash
python -m pytest tests/ -v --ignore=tests/test_playwright_plugins.py
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add templates/settings.html tests/test_settings_manager.py
git commit -m "feat: implement settings page with Gmail test, credential masking, and .env save

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 9: Final Smoke Test + GitHub Push

**Files:** `.gitignore` only

- [ ] **Step 1: Ensure .env and .superpowers are gitignored**

```bash
cd /Users/nalinpatel/ai_consulting_business
grep -q "^\.env$" .gitignore 2>/dev/null || echo ".env" >> .gitignore
grep -q "\.superpowers" .gitignore 2>/dev/null || echo ".superpowers/" >> .gitignore
```

- [ ] **Step 2: Run full test suite**

```bash
python -m pytest tests/ -v --ignore=tests/test_playwright_plugins.py
```

Expected: All PASS. If anything fails, fix before proceeding.

- [ ] **Step 3: Start app and manually verify all 7 pages**

```bash
python app.py
```

Checklist — open each in browser:
- [ ] http://localhost:5000/login — login form renders
- [ ] http://localhost:5000 — dashboard with stat cards and leads table
- [ ] http://localhost:5000/scraper — form + run button + progress card appears on submit
- [ ] http://localhost:5000/leads — leads table with search and Export Excel button
- [ ] http://localhost:5000/outreach — queue tabs load, warning if no Gmail
- [ ] http://localhost:5000/content — generate button works, posts display
- [ ] http://localhost:5000/plugins — 27 plugin toggles across 4 groups
- [ ] http://localhost:5000/settings — 4 credential cards, Save All and Test Connection work

- [ ] **Step 4: Commit .gitignore and push to GitHub**

```bash
git add .gitignore
git commit -m "chore: gitignore .env and .superpowers/

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
git push origin main
```

Expected: Push succeeds to https://github.com/Adnovation01/MACBOOK-CLAUDE-MEMORY
