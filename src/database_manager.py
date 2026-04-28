import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'mission_control.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Leads Table
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
        except sqlite3.OperationalError as e:
            if 'duplicate column name' not in str(e):
                raise
    
    # Missions Table (Track who is scraping what)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS missions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            industry TEXT,
            status TEXT DEFAULT 'Running',
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_lead(lead_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO leads (name, website, email, location, niche, leak_amount, pain_points)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        lead_data['name'], 
        lead_data['url'], 
        lead_data['email'], 
        lead_data['location'], 
        lead_data['niche'],
        lead_data['analysis']['estimated_revenue_leak'],
        json.dumps(lead_data['analysis']['hard_pain_points'])
    ))
    conn.commit()
    conn.close()

def get_all_leads():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM leads ORDER BY id DESC')
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def update_lead_action(lead_id, action):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE leads SET action = ? WHERE id = ?', (action, lead_id))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Mission Control Database Initialized for Cloud Deployment.")
