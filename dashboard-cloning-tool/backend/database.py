import sqlite3
import os
import bcrypt
from datetime import datetime
from config import config

DB_PATH = config.get_db_path()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    c = conn.cursor()

    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            role TEXT NOT NULL DEFAULT 'user',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now')),
            last_login TEXT
        );

        CREATE TABLE IF NOT EXISTS invites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            token TEXT UNIQUE NOT NULL,
            invited_by TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS clone_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            client_name TEXT NOT NULL,
            dashboard_name TEXT NOT NULL,
            table_name TEXT NOT NULL,
            output_file TEXT,
            status TEXT DEFAULT 'success',
            error_msg TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    ''')
    conn.commit()

    # Create super admin if not exists
    existing = c.execute('SELECT id FROM users WHERE email = ?', (config.SUPER_ADMIN_EMAIL,)).fetchone()
    if not existing:
        pw_hash = bcrypt.hashpw(config.SUPER_ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
        c.execute(
            'INSERT INTO users (email, password_hash, name, role, status) VALUES (?, ?, ?, ?, ?)',
            (config.SUPER_ADMIN_EMAIL, pw_hash, 'Super Admin', 'superadmin', 'active')
        )
        conn.commit()
        print(f"[DB] Super admin created: {config.SUPER_ADMIN_EMAIL}")

    conn.close()

# --- User helpers ---

def get_user_by_email(email: str):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_all_users():
    conn = get_db()
    users = conn.execute('SELECT id, email, name, role, status, created_at, last_login FROM users ORDER BY created_at DESC').fetchall()
    conn.close()
    return [dict(u) for u in users]

def create_user(email: str, password: str, name: str, role: str):
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = get_db()
    conn.execute(
        'INSERT INTO users (email, password_hash, name, role, status) VALUES (?, ?, ?, ?, ?)',
        (email, pw_hash, name, role, 'active')
    )
    conn.commit()
    conn.close()

def update_user_role(email: str, role: str):
    conn = get_db()
    conn.execute('UPDATE users SET role = ? WHERE email = ?', (role, email))
    conn.commit()
    conn.close()

def remove_user(email: str):
    conn = get_db()
    conn.execute('DELETE FROM users WHERE email = ?', (email,))
    conn.commit()
    conn.close()

def update_last_login(email: str):
    conn = get_db()
    conn.execute('UPDATE users SET last_login = ? WHERE email = ?', (datetime.utcnow().isoformat(), email))
    conn.commit()
    conn.close()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def update_credentials(section: str, updates: dict):
    """Update .env file with new credentials"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    with open(env_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        replaced = False
        for key, val in updates.items():
            if line.startswith(f"{key}="):
                new_lines.append(f"{key}={val}\n")
                replaced = True
                break
        if not replaced:
            new_lines.append(line)

    with open(env_path, 'w') as f:
        f.writelines(new_lines)

# --- Invite helpers ---

def create_invite(email: str, role: str, token: str, invited_by: str, expires_at: str):
    conn = get_db()
    # Remove any existing unused invite for this email
    conn.execute('DELETE FROM invites WHERE email = ? AND used = 0', (email,))
    conn.execute(
        'INSERT INTO invites (email, role, token, invited_by, expires_at) VALUES (?, ?, ?, ?, ?)',
        (email, role, token, invited_by, expires_at)
    )
    conn.commit()
    conn.close()

def get_invite_by_token(token: str):
    conn = get_db()
    invite = conn.execute('SELECT * FROM invites WHERE token = ? AND used = 0', (token,)).fetchone()
    conn.close()
    return dict(invite) if invite else None

def mark_invite_used(token: str):
    conn = get_db()
    conn.execute('UPDATE invites SET used = 1 WHERE token = ?', (token,))
    conn.commit()
    conn.close()

def get_all_invites():
    conn = get_db()
    invites = conn.execute('SELECT * FROM invites ORDER BY created_at DESC').fetchall()
    conn.close()
    return [dict(i) for i in invites]

# --- Clone history ---

def log_clone(user_email, client_name, dashboard_name, table_name, output_file, status='success', error_msg=None):
    conn = get_db()
    conn.execute(
        'INSERT INTO clone_history (user_email, client_name, dashboard_name, table_name, output_file, status, error_msg) VALUES (?,?,?,?,?,?,?)',
        (user_email, client_name, dashboard_name, table_name, output_file, status, error_msg)
    )
    conn.commit()
    conn.close()

def get_history(user_email=None, role=None):
    conn = get_db()
    if role in ('superadmin', 'admin'):
        rows = conn.execute('SELECT * FROM clone_history ORDER BY created_at DESC').fetchall()
    else:
        rows = conn.execute('SELECT * FROM clone_history WHERE user_email = ? ORDER BY created_at DESC', (user_email,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
