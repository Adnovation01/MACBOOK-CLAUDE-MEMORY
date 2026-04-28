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

# -- Auth ---------------------------------------------------------------------

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

# -- Page routes --------------------------------------------------------------

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
        total_leads=len(all_leads), emails_sent=emails_sent,
        queue_due=queue_due, recent_leads=all_leads[:10])

@app.route('/scraper')
@login_required
def scraper():
    return render_template('scraper.html', active='scraper')

@app.route('/leads')
@login_required
def leads():
    all_leads = get_all_leads()
    niches = sorted(set(l.get('niche', '') for l in all_leads if l.get('niche')))
    return render_template('leads.html', active='leads', leads=all_leads, niches=niches)

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

@app.route('/content')
@login_required
def content():
    posts = []
    content_path = 'data/marketing_content.json'
    if os.path.exists(content_path):
        with open(content_path) as f:
            posts = json.load(f)
    return render_template('content.html', active='content', posts=posts)

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

# -- Existing API (unchanged) -------------------------------------------------

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
                        'current_plugin': 'starting...', 'error': None}
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
    except Exception:
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
        return jsonify({'status': 'success', 'message': 'Gmail connection successful!'})
    except smtplib.SMTPAuthenticationError:
        return jsonify({'status': 'error',
                        'message': 'Authentication failed — use an App Password, not your account password.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
