import json
import sqlite3
from datetime import datetime, timezone
from app.models.wellness import JournalEntry, JournalAnalysis, MoodLog


def get_db_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # Create journals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS journals (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            exam_context TEXT,
            created_at TEXT NOT NULL,
            analysis TEXT NOT NULL,
            user_id TEXT
        )
    """)
    
    # Create mood logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mood_logs (
            id TEXT PRIMARY KEY,
            mood_score INTEGER NOT NULL,
            energy_level INTEGER,
            sleep_hours REAL,
            study_hours REAL,
            stress_level INTEGER,
            note TEXT,
            created_at TEXT NOT NULL,
            user_id TEXT
        )
    """)
    
    # Schema migration checks (if tables already existed without user_id)
    try:
        cursor.execute("ALTER TABLE journals ADD COLUMN user_id TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        cursor.execute("ALTER TABLE mood_logs ADD COLUMN user_id TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Indexes for quick access
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_journals_user_created ON journals(user_id, created_at DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mood_logs_user_created ON mood_logs(user_id, created_at DESC)")
    
    conn.commit()
    conn.close()


# User Operations
def save_user(db_path: str, user_id: str, username: str, password_hash: str) -> None:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (id, username, password_hash, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, username, password_hash, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()


def get_user_by_username(db_path: str, username: str) -> dict | None:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, created_at FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_user_by_id(db_path: str, user_id: str) -> dict | None:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, created_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


# Journal Operations (Partitioned by user_id)
def save_journal(db_path: str, entry: JournalEntry, user_id: str) -> None:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO journals (id, content, exam_context, created_at, analysis, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            entry.id,
            entry.content,
            entry.exam_context,
            entry.created_at.isoformat(),
            entry.analysis.model_dump_json(),
            user_id
        )
    )
    conn.commit()
    conn.close()


def get_journals(db_path: str, user_id: str, limit: int | None = None) -> list[JournalEntry]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    query = "SELECT id, content, exam_context, created_at, analysis FROM journals WHERE user_id = ? ORDER BY created_at DESC"
    params = [user_id]
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    entries = []
    for row in rows:
        analysis_data = json.loads(row["analysis"])
        created_at_dt = datetime.fromisoformat(row["created_at"])
        entry = JournalEntry(
            id=row["id"],
            content=row["content"],
            exam_context=row["exam_context"],
            created_at=created_at_dt,
            analysis=JournalAnalysis(**analysis_data)
        )
        entries.append(entry)
    return entries


# Mood Log Operations (Partitioned by user_id)
def save_mood_log(db_path: str, log: MoodLog, user_id: str) -> None:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO mood_logs (id, mood_score, energy_level, sleep_hours, study_hours, stress_level, note, created_at, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            log.id,
            log.mood_score,
            log.energy_level,
            log.sleep_hours,
            log.study_hours,
            log.stress_level,
            log.note,
            log.created_at.isoformat(),
            user_id
        )
    )
    conn.commit()
    conn.close()


def get_mood_logs(db_path: str, user_id: str, limit: int | None = None) -> list[MoodLog]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    query = "SELECT id, mood_score, energy_level, sleep_hours, study_hours, stress_level, note, created_at FROM mood_logs WHERE user_id = ? ORDER BY created_at DESC"
    params = [user_id]
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    logs = []
    for row in rows:
        created_at_dt = datetime.fromisoformat(row["created_at"])
        log = MoodLog(
            id=row["id"],
            mood_score=row["mood_score"],
            energy_level=row["energy_level"],
            sleep_hours=row["sleep_hours"],
            study_hours=row["study_hours"],
            stress_level=row["stress_level"],
            note=row["note"],
            created_at=created_at_dt
        )
        logs.append(log)
    return logs


def get_counts(db_path: str, user_id: str) -> tuple[int, int]:
    """Retrieve fast database count records for dashboard summary partitioned by user."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM journals WHERE user_id = ?", (user_id,))
    journal_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM mood_logs WHERE user_id = ?", (user_id,))
    mood_count = cursor.fetchone()[0]
    conn.close()
    return journal_count, mood_count


def clear_db(db_path: str) -> None:
    """Utility function to clear database tables (used for testing)."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM journals")
    cursor.execute("DELETE FROM mood_logs")
    cursor.execute("DELETE FROM users")
    conn.commit()
    conn.close()
