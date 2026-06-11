import sqlite3
import hashlib
import os
import json

# ─── Settings helpers ────────────────────────────────────────────────────────

def _ensure_settings_table(db):
    """Create settings table if not exists — safe to call multiple times"""
    try:
        db.execute("""CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        )""")
        db.commit()
    except Exception:
        pass

def get_setting(key: str, default: str = '') -> str:
    db = get_db()
    try:
        _ensure_settings_table(db)
        row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row['value'] if row else default
    except Exception:
        return default
    finally:
        try:
            db.close()
        except Exception:
            pass

def set_setting(key: str, value: str):
    db = get_db()
    try:
        _ensure_settings_table(db)
        if _is_postgres():
            # PostgreSQL upsert
            db.execute(
                "INSERT INTO settings (key, value) VALUES (?,?) ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value",
                (key, value)
            )
        else:
            # SQLite upsert
            db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))
        db.commit()
    finally:
        try:
            db.close()
        except Exception:
            pass

DATABASE_URL = os.environ.get("DATABASE_URL", "")

def hash_password(password):
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(plain: str, stored: str) -> bool:
    """תומך במעבר: SHA-256 ישן (64 תווים hex) ו-bcrypt חדש ($2b$...)"""
    import bcrypt, hashlib
    if stored.startswith("$2b$") or stored.startswith("$2a$"):
        return bcrypt.checkpw(plain.encode(), stored.encode())
    # legacy SHA-256 — השווה ואפשר migration בlogin
    return hashlib.sha256(plain.encode()).hexdigest() == stored

def _is_postgres():
    return bool(DATABASE_URL and ("postgres" in DATABASE_URL))

class _PgRow:
    """Row that supports both integer index and key access, like sqlite3.Row"""
    def __init__(self, values, description):
        self._values = list(values)
        self._keys = [d[0].lower() for d in description]

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._values[self._keys.index(key.lower())]

    def __contains__(self, key):
        return key.lower() in self._keys

    def keys(self):
        return self._keys

    def __iter__(self):
        return iter(self._keys)

    def __repr__(self):
        return str(dict(zip(self._keys, self._values)))


class _PgCursor:
    """Cursor wrapper that returns _PgRow objects"""
    def __init__(self, cur):
        self._cur = cur

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        return _PgRow(row, self._cur.description)

    def fetchall(self):
        rows = self._cur.fetchall()
        if not rows:
            return []
        return [_PgRow(row, self._cur.description) for row in rows]

    def __iter__(self):
        for row in self._cur:
            yield _PgRow(row, self._cur.description)

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    @property
    def rowcount(self):
        return self._cur.rowcount


class _PgWrapper:
    """Thin wrapper around psycopg2 connection to mimic sqlite3 interface"""
    def __init__(self, conn):
        self._conn = conn

    def _convert(self, query):
        import re
        # NOTE: re.sub replaces ALL '?' including ones inside string literals.
        # Verified that no query in this codebase embeds a literal '?' inside
        # a quoted string value — all '?' occurrences are SQL parameter placeholders.
        # If that changes, a parser that skips quoted regions will be needed here.
        pg_query = re.sub(r'\?', '%s', query)
        pg_query = pg_query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        pg_query = pg_query.replace("autoincrement", "")
        return pg_query

    def execute(self, query, params=()):
        cur = self._conn.cursor()
        cur.execute(self._convert(query), params)
        return _PgCursor(cur)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

    def rollback(self):
        self._conn.rollback()

    def executemany(self, query, params_list):
        cur = self._conn.cursor()
        cur.executemany(self._convert(query), params_list)
        return _PgCursor(cur)


def get_db():
    if _is_postgres():
        import psycopg2
        url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url)
        conn.autocommit = False
        return _PgWrapper(conn)
    else:
        conn = sqlite3.connect("sales.db", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    db = get_db()

    if _is_postgres():
        # PostgreSQL CREATE TABLE
        stmts = [
            """CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'agent',
                regions TEXT NOT NULL DEFAULT ''
            )""",
            """CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                card_code TEXT,
                name TEXT NOT NULL,
                city TEXT,
                address TEXT,
                region TEXT,
                delivery_day TEXT,
                x_days INTEGER,
                visit_day TEXT,
                traffic_light TEXT,
                assigned_visit_day TEXT,
                week_1 INTEGER DEFAULT 0,
                week_2 INTEGER DEFAULT 0,
                week_3 INTEGER DEFAULT 0,
                week_4 INTEGER DEFAULT 0,
                week_5 INTEGER DEFAULT 0,
                week_6 INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS visits (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                visit_date TEXT NOT NULL,
                check_in_time TEXT,
                check_out_time TEXT,
                duration_minutes INTEGER,
                notes TEXT,
                paused_at TEXT,
                pause_duration_minutes INTEGER DEFAULT 0,
                is_phone INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                message TEXT NOT NULL,
                user_name TEXT,
                store_name TEXT,
                action TEXT,
                created_at TEXT NOT NULL,
                is_read INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS visit_comments (
                id SERIAL PRIMARY KEY,
                visit_id INTEGER,
                customer_id INTEGER NOT NULL,
                visit_date TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                user_role TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_read INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT ''
            )""",
            """CREATE TABLE IF NOT EXISTS push_subscriptions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                endpoint TEXT NOT NULL,
                p256dh TEXT NOT NULL,
                auth TEXT NOT NULL,
                created_at TEXT NOT NULL
            )""",
            """ALTER TABLE users ADD COLUMN IF NOT EXISTS beep_sound INTEGER DEFAULT 4""",
            """ALTER TABLE customers ADD COLUMN IF NOT EXISTS week_5 INTEGER DEFAULT 0""",
            """ALTER TABLE customers ADD COLUMN IF NOT EXISTS week_6 INTEGER DEFAULT 0""",
            """ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_phone INTEGER DEFAULT 0""",
        ]
        for stmt in stmts:
            db.execute(stmt)
    else:
        # SQLite CREATE TABLE (original)
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'agent',
            regions TEXT NOT NULL DEFAULT ''
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_code TEXT,
            name TEXT NOT NULL,
            city TEXT,
            address TEXT,
            region TEXT,
            delivery_day TEXT,
            x_days INTEGER,
            visit_day TEXT,
            traffic_light TEXT,
            assigned_visit_day TEXT,
            week_1 INTEGER DEFAULT 0,
            week_2 INTEGER DEFAULT 0,
            week_3 INTEGER DEFAULT 0,
            week_4 INTEGER DEFAULT 0
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            visit_date TEXT NOT NULL,
            check_in_time TEXT,
            check_out_time TEXT,
            duration_minutes INTEGER,
            notes TEXT,
            paused_at TEXT,
            pause_duration_minutes INTEGER DEFAULT 0,
            is_phone INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            user_name TEXT,
            store_name TEXT,
            action TEXT,
            created_at TEXT NOT NULL,
            is_read INTEGER DEFAULT 0
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS visit_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER,
            customer_id INTEGER NOT NULL,
            visit_date TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            user_role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS push_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            endpoint TEXT NOT NULL,
            p256dh TEXT NOT NULL,
            auth TEXT NOT NULL,
            created_at TEXT NOT NULL
        )''')

        # SQLite migrations for older DBs — customers
        for col, coldef in [
            ('traffic_light',     'TEXT'),
            ('assigned_visit_day','TEXT'),
            ('week_1',            'INTEGER DEFAULT 0'),
            ('week_2',            'INTEGER DEFAULT 0'),
            ('week_3',            'INTEGER DEFAULT 0'),
            ('week_4',            'INTEGER DEFAULT 0'),
        ]:
            try:
                db.execute(f'ALTER TABLE customers ADD COLUMN {col} {coldef}')
            except Exception:
                pass
        # SQLite migrations — visits (pause feature)
        for col, coldef in [
            ('paused_at',              'TEXT'),
            ('pause_duration_minutes', 'INTEGER DEFAULT 0'),
        ]:
            try:
                db.execute(f'ALTER TABLE visits ADD COLUMN {col} {coldef}')
            except Exception:
                pass
        # SQLite migrations — visit_comments (is_read)
        try:
            db.execute('ALTER TABLE visit_comments ADD COLUMN is_read INTEGER DEFAULT 0')
        except Exception:
            pass

    import json as _json, pathlib as _pathlib
    _cfg = _json.loads((_pathlib.Path(__file__).parent / "company_config.json").read_text(encoding="utf-8")) if (_pathlib.Path(__file__).parent / "company_config.json").exists() else {}
    _agents = _cfg.get("agents", [
        {"name": "גילי", "username": "gili_agent"},
        {"name": "אלי", "username": "eli"},
        {"name": "שיראל", "username": "shirel"}
    ])

    # Insert default users — passwords from env vars only (never hardcoded)
    _env_key_map = {
        "gili_agent": "AGENT_GILI_PASSWORD",
        "eli":        "AGENT_ELI_PASSWORD",
        "shirel":     "AGENT_SHIREL_PASSWORD",
    }
    user_defs = []
    for _a in _agents:
        _uname = _a["username"]
        _env_key = _env_key_map.get(_uname, f"AGENT_{_uname.upper()}_PASSWORD")
        user_defs.append((_a["name"], _uname, os.environ.get(_env_key), 'agent', ''))
    user_defs.append(('מנהל', 'manager', os.environ.get('MANAGER_PASSWORD'), 'manager', 'all'))
    for name, username, password, role, regions in user_defs:
        if not password:
            continue
        try:
            db.execute(
                'INSERT INTO users (name, username, password_hash, role, regions) VALUES (?,?,?,?,?)',
                (name, username, hash_password(password), role, regions)
            )
        except Exception:
            pass

    db.commit()
    db.close()
