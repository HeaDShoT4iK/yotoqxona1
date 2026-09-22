"""
SQLite (aiosqlite) orqali ma'lumotlar bazasi bilan ishlash.
PostgreSQL talab qilinmaydi — hammasi bitta bot.db faylida saqlanadi.
"""
import aiosqlite

from config import DB_PATH
import utils

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE,
    anon_code TEXT UNIQUE,
    is_blocked INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE,
    full_name TEXT,
    role TEXT DEFAULT 'admin',
    added_by INTEGER,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    text TEXT,
    status TEXT DEFAULT 'yangi',
    group_message_id INTEGER,
    handled_by INTEGER REFERENCES staff(id),
    comment TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS broadcasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    sent_by INTEGER,
    total_sent INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        await conn.executescript(CREATE_TABLES)
        await conn.commit()


def _row_to_dict(cursor, row):
    if row is None:
        return None
    return {d[0]: row[i] for i, d in enumerate(cursor.description)}


# ---------------- USERS ----------------

async def get_or_create_user(telegram_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
        row = await cur.fetchone()
        if row:
            return _row_to_dict(cur, row)

        anon_code = utils.generate_anon_code()
        await conn.execute(
            "INSERT INTO users (telegram_id, anon_code) VALUES (?, ?)",
            (telegram_id, anon_code),
        )
        await conn.commit()
        cur = await conn.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
        row = await cur.fetchone()
        return _row_to_dict(cur, row)


async def get_user_by_id(user_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT * FROM users WHERE id=?", (user_id,))
        row = await cur.fetchone()
        return _row_to_dict(cur, row)


async def set_user_blocked(anon_code: str, blocked: bool) -> bool:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute(
            "UPDATE users SET is_blocked=? WHERE anon_code=?",
            (1 if blocked else 0, anon_code),
        )
        await conn.commit()
        return cur.rowcount > 0


async def list_blocked_users() -> list:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT * FROM users WHERE is_blocked=1")
        rows = await cur.fetchall()
        return [_row_to_dict(cur, r) for r in rows]


# ---------------- STAFF ----------------

async def get_staff(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute(
            "SELECT * FROM staff WHERE telegram_id=? AND is_active=1", (telegram_id,)
        )
        row = await cur.fetchone()
        return _row_to_dict(cur, row)


async def is_super_admin(telegram_id: int) -> bool:
    staff = await get_staff(telegram_id)
    return bool(staff and staff["role"] == "super_admin")


async def add_staff(telegram_id: int, full_name: str, role: str, added_by: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "INSERT INTO staff (telegram_id, full_name, role, added_by, is_active) "
            "VALUES (?, ?, ?, ?, 1) "
            "ON CONFLICT(telegram_id) DO UPDATE SET full_name=excluded.full_name, "
            "role=excluded.role, is_active=1",
            (telegram_id, full_name, role, added_by),
        )
        await conn.commit()


async def deactivate_staff(telegram_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute(
            "UPDATE staff SET is_active=0 WHERE telegram_id=? AND role!='super_admin'",
            (telegram_id,),
        )
        await conn.commit()
        return cur.rowcount > 0


async def list_staff(active_only: bool = True) -> list:
    async with aiosqlite.connect(DB_PATH) as conn:
        query = "SELECT * FROM staff"
        if active_only:
            query += " WHERE is_active=1"
        cur = await conn.execute(query)
        rows = await cur.fetchall()
        return [_row_to_dict(cur, r) for r in rows]


async def ensure_super_admin(telegram_id: int, full_name: str):
    """Bootstrap: .env dagi SUPER_ADMIN_ID birinchi ishga tushishda bazaga qo'shiladi."""
    staff = await get_staff(telegram_id)
    if staff and staff["role"] == "super_admin":
        return
    await add_staff(telegram_id, full_name, "super_admin", added_by=0)


# ---------------- SETTINGS ----------------

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        await conn.commit()


async def get_setting(key: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = await cur.fetchone()
        return row[0] if row else None


# ---------------- TICKETS ----------------

async def create_ticket(user_id: int, text: str) -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute(
            "INSERT INTO tickets (user_id, text) VALUES (?, ?)", (user_id, text)
        )
        await conn.commit()
        return cur.lastrowid


async def set_ticket_group_message(ticket_id: int, message_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE tickets SET group_message_id=? WHERE id=?", (message_id, ticket_id)
        )
        await conn.commit()


async def get_ticket(ticket_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,))
        row = await cur.fetchone()
        return _row_to_dict(cur, row)


async def update_ticket_status(ticket_id: int, status: str, handled_by: int, comment: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE tickets SET status=?, handled_by=?, comment=?, updated_at=datetime('now') "
            "WHERE id=?",
            (status, handled_by, comment, ticket_id),
        )
        await conn.commit()


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT status, COUNT(*) FROM tickets GROUP BY status")
        rows = await cur.fetchall()
        stats = {status: count for status, count in rows}
        cur = await conn.execute("SELECT COUNT(*) FROM tickets")
        total_row = await cur.fetchone()
        stats["jami"] = total_row[0] if total_row else 0
        return stats


# ---------------- BROADCASTS ----------------

async def log_broadcast(text: str, sent_by: int, total_sent: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "INSERT INTO broadcasts (text, sent_by, total_sent) VALUES (?, ?, ?)",
            (text, sent_by, total_sent),
        )
        await conn.commit()


async def list_broadcasts(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute(
            "SELECT * FROM broadcasts ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = await cur.fetchall()
        return [_row_to_dict(cur, r) for r in rows]


async def get_all_user_telegram_ids() -> list:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT telegram_id FROM users WHERE is_blocked=0")
        rows = await cur.fetchall()
        return [r[0] for r in rows]
