
import aiosqlite
from pathlib import Path

DB_PATH = Path("data/chat.db")


async def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS answer_cache (
            cache_key TEXT PRIMARY KEY,
            answer TEXT NOT NULL,
            citations TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        await db.commit()


async def create_session(session_id: str, document_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO sessions(session_id, document_id) VALUES (?, ?)",
            (session_id, document_id),
        )
        await db.commit()


async def get_history(session_id: str, limit: int = 6):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT role, content FROM messages
               WHERE session_id = ?
               ORDER BY id DESC LIMIT ?""",
            (session_id, limit),
        )
        rows = await cursor.fetchall()
    return [{"role": r, "content": c} for r, c in reversed(rows)]


async def save_message(session_id: str, role: str, content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages(session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        await db.commit()


async def get_cached_answer(cache_key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT answer, citations FROM answer_cache
               WHERE cache_key = ?
               AND created_at > datetime('now', '-1 hour')""",
            (cache_key,),
        )
        return await cursor.fetchone()


async def cache_answer(cache_key: str, answer: str, citations: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO answer_cache
               (cache_key, answer, citations) VALUES (?, ?, ?)""",
            (cache_key, answer, citations),
        )
        await db.commit()