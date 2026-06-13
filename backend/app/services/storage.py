from datetime import datetime, timezone
from uuid import uuid4
from app.models.wellness import JournalCreate, JournalEntry, MoodLog, MoodLogCreate
from app.core.config import get_settings
from app.services.ai_analysis import analyze_journal
from app.services.database import (
    init_db,
    save_journal,
    save_mood_log,
    get_journals,
    get_mood_logs,
    clear_db,
    get_counts
)


class SQLiteWellnessStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        init_db(self.db_path)

    def get_recent_journals(self, user_id: str, limit: int | None = None) -> list[JournalEntry]:
        return get_journals(self.db_path, user_id, limit)

    def get_recent_mood_logs(self, user_id: str, limit: int | None = None) -> list[MoodLog]:
        return get_mood_logs(self.db_path, user_id, limit)

    def add_journal(self, payload: JournalCreate, user_id: str) -> JournalEntry:
        analysis = analyze_journal(payload.content)
        entry = JournalEntry(
            id=str(uuid4()),
            content=payload.content,
            exam_context=payload.exam_context,
            created_at=datetime.now(timezone.utc),
            analysis=analysis,
        )
        save_journal(self.db_path, entry, user_id)
        return entry

    def add_mood_log(self, payload: MoodLogCreate, user_id: str) -> MoodLog:
        log = MoodLog(
            id=str(uuid4()),
            created_at=datetime.now(timezone.utc),
            **payload.model_dump()
        )
        save_mood_log(self.db_path, log, user_id)
        return log

    def get_counts(self, user_id: str) -> tuple[int, int]:
        return get_counts(self.db_path, user_id)

    def clear(self) -> None:
        clear_db(self.db_path)


class InMemoryWellnessStore:
    def __init__(self) -> None:
        # Dictionary mapping user_id -> lists
        self.user_journals: dict[str, list[JournalEntry]] = {}
        self.user_mood_logs: dict[str, list[MoodLog]] = {}

    def get_recent_journals(self, user_id: str, limit: int | None = None) -> list[JournalEntry]:
        journals = self.user_journals.get(user_id, [])
        return journals[:limit] if limit is not None else journals

    def get_recent_mood_logs(self, user_id: str, limit: int | None = None) -> list[MoodLog]:
        logs = self.user_mood_logs.get(user_id, [])
        return logs[:limit] if limit is not None else logs

    def add_journal(self, payload: JournalCreate, user_id: str) -> JournalEntry:
        entry = JournalEntry(
            id=str(uuid4()),
            content=payload.content,
            exam_context=payload.exam_context,
            created_at=datetime.now(timezone.utc),
            analysis=analyze_journal(payload.content),
        )
        if user_id not in self.user_journals:
            self.user_journals[user_id] = []
        self.user_journals[user_id].insert(0, entry)
        return entry

    def add_mood_log(self, payload: MoodLogCreate, user_id: str) -> MoodLog:
        log = MoodLog(
            id=str(uuid4()), 
            created_at=datetime.now(timezone.utc), 
            **payload.model_dump()
        )
        if user_id not in self.user_mood_logs:
            self.user_mood_logs[user_id] = []
        self.user_mood_logs[user_id].insert(0, log)
        return log

    def get_counts(self, user_id: str) -> tuple[int, int]:
        return (
            len(self.user_journals.get(user_id, [])),
            len(self.user_mood_logs.get(user_id, []))
        )

    def clear(self) -> None:
        self.user_journals = {}
        self.user_mood_logs = {}


# Initialize store using settings
settings = get_settings()
store = SQLiteWellnessStore(settings.db_path)
