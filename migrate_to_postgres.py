"""
migrate_to_postgres.py — העברת נתונים מ-SQLite לפוסטגרס (הרצה חד-פעמית)

שימוש:
  1. הגדר DATABASE_URL=<postgresql://...> בסביבה
  2. הרץ: python migrate_to_postgres.py

אפשרות שחזור מגיבוי JSON:
  python migrate_to_postgres.py --from-json backup_unico_2026-05-17_1638.json
"""
import os
import sys
import json
import sqlite3
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL", "")
SQLITE_PATH  = os.environ.get("DB_PATH", "sales.db")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL is not set.")
    sys.exit(1)

pg_url = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def get_pg():
    conn = psycopg2.connect(pg_url)
    conn.autocommit = False
    return conn

def get_sqlite():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables(pg):
    cur = pg.cursor()
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
            week_4 INTEGER DEFAULT 0
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
            is_phone INTEGER DEFAULT 0,
            paused_at TEXT,
            pause_duration_minutes INTEGER DEFAULT 0
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
    ]
    for stmt in stmts:
        cur.execute(stmt)
    pg.commit()
    print("Tables created/verified.")

def reset_sequences(pg):
    """עדכון SERIAL sequences אחרי import ידני עם IDs מפורשים"""
    cur = pg.cursor()
    for table in ['users', 'customers', 'visits', 'notifications', 'visit_comments', 'push_subscriptions']:
        cur.execute(f"SELECT setval('{table}_id_seq', COALESCE((SELECT MAX(id) FROM {table}), 1))")
    pg.commit()
    print("Sequences reset.")

def migrate_from_sqlite():
    print(f"Reading from SQLite: {SQLITE_PATH}")
    sq = get_sqlite()
    pg = get_pg()
    create_tables(pg)
    cur_pg = pg.cursor()

    tables = ['users', 'customers', 'visits', 'notifications', 'visit_comments', 'settings', 'push_subscriptions']
    for table in tables:
        try:
            rows = sq.execute(f"SELECT * FROM {table}").fetchall()
        except Exception as e:
            print(f"  {table}: skip ({e})")
            continue

        if not rows:
            print(f"  {table}: 0 rows")
            continue

        cols   = list(rows[0].keys())
        ph     = ','.join(['%s'] * len(cols))
        col_str = ','.join(cols)
        sql    = f"INSERT INTO {table} ({col_str}) VALUES ({ph}) ON CONFLICT DO NOTHING"

        count = 0
        for row in rows:
            try:
                cur_pg.execute(sql, list(row))
                count += 1
            except Exception as e:
                print(f"    row error in {table}: {e}")
                pg.rollback()
        pg.commit()
        print(f"  {table}: {count}/{len(rows)} rows migrated")

    reset_sequences(pg)
    sq.close()
    pg.close()
    print("\nMigration from SQLite complete.")

def migrate_from_json(json_path):
    print(f"Reading from JSON backup: {json_path}")
    with open(json_path, encoding='utf-8') as f:
        backup = json.load(f)

    pg = get_pg()
    create_tables(pg)
    cur_pg = pg.cursor()

    for table, rows in backup.items():
        if not rows:
            print(f"  {table}: 0 rows")
            continue

        cols   = list(rows[0].keys())
        ph     = ','.join(['%s'] * len(cols))
        col_str = ','.join(cols)
        sql    = f"INSERT INTO {table} ({col_str}) VALUES ({ph}) ON CONFLICT DO NOTHING"

        count = 0
        for row in rows:
            try:
                cur_pg.execute(sql, [row.get(c) for c in cols])
                count += 1
            except Exception as e:
                print(f"    row error in {table}: {e}")
                pg.rollback()
        pg.commit()
        print(f"  {table}: {count}/{len(rows)} rows imported")

    reset_sequences(pg)
    pg.close()
    print("\nRestore from JSON complete.")

if __name__ == "__main__":
    if "--from-json" in sys.argv:
        idx = sys.argv.index("--from-json")
        if idx + 1 >= len(sys.argv):
            print("ERROR: missing JSON path after --from-json")
            sys.exit(1)
        migrate_from_json(sys.argv[idx + 1])
    else:
        migrate_from_sqlite()
