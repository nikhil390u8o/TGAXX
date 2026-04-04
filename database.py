import sqlite3
from config import BASE_SESSION_DIR


def get_db():
    return sqlite3.connect("database.db", timeout=60, check_same_thread=False)


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        balance REAL DEFAULT 0,
        total_spent REAL DEFAULT 0,
        total_deposited REAL DEFAULT 0
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        session_name TEXT,
        status INTEGER DEFAULT 0,
        country TEXT,
        price REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        password TEXT,
        last_otp TEXT
    )""")
    cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    cur.execute("""CREATE TABLE IF NOT EXISTS country_prices (
        country TEXT PRIMARY KEY,
        price REAL
    )""")
    cur.execute("CREATE TABLE IF NOT EXISTS business_stats (key TEXT PRIMARY KEY, value REAL)")
    cur.execute("INSERT OR IGNORE INTO settings VALUES ('price','100')")
    cur.execute("INSERT OR IGNORE INTO business_stats VALUES ('total_sold',0), ('total_revenue',0), ('total_deposited',0)")
    conn.commit()
    conn.close()


def get_user_data(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT balance, total_spent, total_deposited FROM users WHERE id=?", (user_id,))
    res = cur.fetchone()
    if not res:
        cur.execute("INSERT INTO users VALUES (?,0,0,0)", (user_id,))
        conn.commit()
        conn.close()
        return (0, 0, 0)
    conn.close()
    return res


def update_user_stats(user_id, balance_delta=0, spent_delta=0, deposit_delta=0):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET balance = balance + ?, total_spent = total_spent + ?, total_deposited = total_deposited + ? WHERE id = ?",
        (balance_delta, spent_delta, deposit_delta, user_id))
    conn.commit()
    conn.close()


def update_biz_stats(key, amount):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE business_stats SET value = value + ? WHERE key=?", (amount, key))
    conn.commit()
    conn.close()


def get_setting(key):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = cur.fetchone()
    conn.close()
    return res[0] if res else "100"


def get_country_price(country):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT price FROM country_prices WHERE country=?", (country,))
    row = cur.fetchone()
    conn.close()
    if row:
        return float(row[0])
    return float(get_setting("price"))


def set_country_price(country, price):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO country_prices (country, price)
    VALUES (?, ?)
    ON CONFLICT(country) DO UPDATE SET price=excluded.price
    """, (country, price))
    conn.commit()
    conn.close()
