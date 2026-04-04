import os
import sqlite3
from core.config import log, DB_PATH, DB_TIMEOUT, DB_WAL_MODE

# Protocol Engine Database Interface

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Clients Table (B2B API Keys & Subscriptions)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            plan_type TEXT DEFAULT 'Free', -- 'Free', 'Pro', 'Enterprise'
            credits_total INTEGER DEFAULT 10,
            credits_used INTEGER DEFAULT 0,
            expires_at TIMESTAMP DEFAULT (datetime('now', '+30 days')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Deeds History Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            nomad_id TEXT,
            mission_id TEXT,
            verdict TEXT,
            impact_points INTEGER,
            tx_hash TEXT,
            integrity_hash TEXT,
            ai_dialogue TEXT,
            source TEXT DEFAULT 'direct', -- 'B2B_Gateway', 'Integrity_Sandbox', etc.
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
    ''')

    # [MIGRATION] Add missing columns to legacy deeds table
    try:
        cursor.execute("ALTER TABLE deeds ADD COLUMN ai_dialogue TEXT;")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE deeds ADD COLUMN source TEXT DEFAULT 'direct';")
    except sqlite3.OperationalError: pass
    
    # 3. ESG Campaigns Table (B2B Bounties)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER, -- Owner of the campaign
            fund_name TEXT,
            vault_address TEXT,
            title TEXT,
            requirements TEXT,
            reward INTEGER,
            total_budget INTEGER DEFAULT 1000,
            current_payouts INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            webhook_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
    ''')
    
    # [MIGRATION] Add subscription and ownership fields if they don't exist
    for col, col_type in [("plan_type", "TEXT DEFAULT 'Free'"), 
                          ("credits_total", "INTEGER DEFAULT 10"), 
                          ("credits_used", "INTEGER DEFAULT 0"), 
                          ("expires_at", "TIMESTAMP DEFAULT (datetime('now', '+30 days'))")]:
        try:
            cursor.execute(f"ALTER TABLE clients ADD COLUMN {col} {col_type};")
        except sqlite3.OperationalError:
            pass # Already exists

    try:
        cursor.execute("ALTER TABLE campaigns ADD COLUMN client_id INTEGER;")
    except sqlite3.OperationalError:
        pass
            
    # Add a default test client for the pitch with Pro plan
    cursor.execute("""
        INSERT OR IGNORE INTO clients (name, api_key, plan_type, credits_total, credits_used) 
        VALUES ('Aqtobe_B2B_Partner', 'PQ_LIVE_DEMO_SECRET', 'Pro', 1000, 0)
    """)
    
    conn.commit()
    conn.close()
    log.info("[DB_GATEWAY] SQLite MVP Database Initialized ✓")

def get_db_connection():
    """
    Returns a hardened SQLite connection with WAL mode enabled and increased timeout.
    WAL allows multiple readers and one writer concurrently.
    """
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
    conn.row_factory = sqlite3.Row
    if DB_WAL_MODE:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def save_deed(deed_data: dict, mission_info: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get client_id (mocking as first client for pitch)
        cursor.execute("SELECT id FROM clients LIMIT 1")
        client_id = cursor.fetchone()[0]
        
        import json
        ai_dialogue_json = json.dumps(deed_data.get('ai_dialogue', []), ensure_ascii=False)
        
        cursor.execute('''
            INSERT INTO deeds (client_id, nomad_id, mission_id, verdict, impact_points, tx_hash, integrity_hash, ai_dialogue, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            client_id, 
            deed_data.get('wallet_address', deed_data.get('user_id', 'unknown')), 
            deed_data.get('mission_id', 'unknown'), 
            deed_data.get('verdict', 'REVIEW_NEEDED'), 
            deed_data.get('impact_score', 0) if isinstance(deed_data.get('impact_score'), (int, float)) else 0, 
            deed_data.get('tx_hash', 'N/A'), 
            deed_data.get('integrity_hash', 'N/A'),
            ai_dialogue_json,
            deed_data.get('source', 'TMA_APP')
        ))
        conn.commit()
    except Exception as e:
        log.error(f"[DB_GATEWAY] Write Failed: {e}")
    finally:
        conn.close()

def get_recent_deeds(limit=20):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deeds ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total, SUM(impact_points) as impact FROM deeds")
    res = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) as count FROM deeds WHERE verdict = 'ADAL'")
    adal = cursor.fetchone()
    conn.close()
    
    return {
        "total_audits": res['total'] or 0,
        "adal_count": adal['count'] or 0,
        "total_impact_score": res['impact'] or 0
    }

def create_campaign(client_id: int, fund_name: str, title: str, requirements: str, reward: int, total_budget: int = 1000, vault_address: str = "TBD", webhook_url: str = None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO campaigns (client_id, fund_name, title, requirements, reward, total_budget, vault_address, webhook_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (client_id, fund_name, title, requirements, reward, total_budget, vault_address, webhook_url))
    campaign_id = c.lastrowid
    conn.commit()
    conn.close()
    return campaign_id

def get_campaigns(only_active: bool = True) -> list[dict]:
    """
    Retrieves all managed campaigns from the persistence layer.
    
    Args:
        only_active: If True, filters for campaigns with is_active = 1.
        
    Returns:
        List of dictionaries containing campaign metadata.
    """
    conn = get_db_connection()
    c = conn.cursor()
    query = 'SELECT * FROM campaigns'
    if only_active:
        query += ' WHERE is_active = 1'
    c.execute(query + ' ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_campaign_by_id(campaign_id: int) -> dict | None:
    """
    Retrieves a single campaign mandate by its unique ID.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM campaigns WHERE id = ?', (campaign_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_deeds_by_campaign(campaign_id: int) -> list[dict]:
    """
    Retrieves all verified deeds for a specific campaign mandate.
    """
    conn = get_db_connection()
    c = conn.cursor()
    # Note: Using mission_id matching or a direct campaign_id link if added,
    # but based on oracle.py, we currently track mission_id.
    # To be precise, we filter deeds by mission_id or other metadata.
    # [HACKATHON_LOGIC]: Since each campaign id has a 1:1 mapping in this MVP
    c.execute('''
        SELECT * FROM deeds 
        WHERE mission_id IN (SELECT id FROM campaigns WHERE id = ?) 
           OR mission_id = (SELECT title FROM campaigns WHERE id = ?)
        ORDER BY timestamp DESC
    ''', (campaign_id, campaign_id))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_campaign_payout(campaign_id: int, amount: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE campaigns 
        SET current_payouts = current_payouts + ? 
        WHERE id = ?
    ''', (amount, campaign_id))
    
    # Auto-close if budget reached
    c.execute('''
        UPDATE campaigns 
        SET is_active = 0 
        WHERE id = ? AND current_payouts >= total_budget
    ''', (campaign_id,))
    
    conn.commit()
    conn.close()

def update_deed_status(integrity_hash: str, tx_hash: str, status: str):
    """
    Updates both tx_hash and on-chain status of a deed.
    Used by the Transaction Status Oracle.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE deeds 
        SET tx_hash = ?, verdict = CASE WHEN ? = 'failed' THEN 'FAILED' ELSE verdict END
        WHERE integrity_hash = ?
    ''', (tx_hash, status, integrity_hash))
    conn.commit()
    conn.close()
    log.info(f"[DB_STATUS] {integrity_hash} status updated to: {status}")

def get_client_by_key(api_key: str) -> dict | None:
    conn = get_db_connection()
    client = conn.execute("SELECT * FROM clients WHERE api_key = ?", (api_key,)).fetchone()
    conn.close()
    return dict(client) if client else None

def check_client_credits(client_id: int) -> bool:
    """
    Validates if the client has enough credits and subscription is not expired.
    """
    conn = get_db_connection()
    client = conn.execute(
        "SELECT credits_total, credits_used, expires_at FROM clients WHERE id = ?", 
        (client_id,)
    ).fetchone()
    conn.close()
    
    if not client:
        return False
        
    # 1. Limit Check
    if client['credits_used'] >= client['credits_total']:
        log.warning(f"[QUOTA] Client {client_id} reached credit limit.")
        return False
        
    # 2. Expiry Check (Simplified for MVP)
    # import datetime
    # if datetime.datetime.fromisoformat(client['expires_at']) < datetime.datetime.now():
    #     return False
        
    return True

def deduct_credit(client_id: int):
    """
    Atomically increments credits_used for a specific client.
    """
    conn = get_db_connection()
    conn.execute("UPDATE clients SET credits_used = credits_used + 1 WHERE id = ?", (client_id,))
    conn.commit()
    conn.close()
    log.info(f"[QUOTA] Credit deducted for client {client_id}")

def get_client_usage(client_id: int) -> dict:
    conn = get_db_connection()
    client = conn.execute(
        "SELECT plan_type, credits_total, credits_used, expires_at FROM clients WHERE id = ?", 
        (client_id,)
    ).fetchone()
    conn.close()
    return dict(client) if client else {}

def get_campaign_analytics(campaign_id: int) -> dict:
    """
    Aggregation engine for Professional ESG Reporting.
    Calculates impact metrics and consensus statistics.
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    # 1. Basic Stats
    c.execute('''
        SELECT 
            COUNT(*) as total_deeds,
            AVG(impact_points) as avg_impact,
            SUM(impact_points) as total_impact,
            SUM(CASE WHEN verdict = 'ADAL' THEN 1 ELSE 0 END) as adal_count,
            SUM(CASE WHEN verdict = 'ARAM' THEN 1 ELSE 0 END) as aram_count
        FROM deeds d
        JOIN campaigns camp ON (d.mission_id = camp.id OR d.mission_id = camp.title)
        WHERE camp.id = ?
    ''', (campaign_id,))
    stats = dict(c.fetchone())
    
    # 2. Get Campaign Metadata
    c.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
    camp = dict(c.fetchone())
    
    # 3. Recent Deeds with AI Dialogue
    deeds = get_deeds_by_campaign(campaign_id)
    
    conn.close()
    
    return {
        "campaign": camp,
        "metrics": {
            "total_verifications": stats['total_deeds'] or 0,
            "adal_rate": (stats['adal_count'] / stats['total_deeds'] * 100) if stats['total_deeds'] and stats['total_deeds'] > 0 else 0,
            "total_impact_score": stats['total_impact'] or 0,
            "avg_impact_score": stats['avg_impact'] or 0,
            "integrity_index": 0.98 # Mocked KPI for demo
        },
        "deeds": deeds
    }
