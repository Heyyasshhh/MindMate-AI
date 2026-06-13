import os
from datetime import datetime, timezone
from app.models.wellness import JournalEntry, JournalAnalysis, RiskLevel, MoodLog
from app.services.database import (
    init_db,
    save_journal,
    get_journals,
    save_mood_log,
    get_mood_logs,
    get_counts,
    save_user,
    get_user_by_username
)


def test_sqlite_persistence() -> None:
    db_path = "test_mindmate.db"
    user_id_1 = "user-abc-123"
    user_id_2 = "user-xyz-789"
    
    if os.path.exists(db_path):
        os.remove(db_path)
        
    try:
        init_db(db_path)
        
        # Save users
        save_user(db_path, user_id_1, "student_one", "hash_one")
        save_user(db_path, user_id_2, "student_two", "hash_two")
        
        # Verify user lookups
        u1 = get_user_by_username(db_path, "student_one")
        assert u1 is not None
        assert u1["id"] == user_id_1
        
        # Verify tables are empty for user 1
        journals_1 = get_journals(db_path, user_id_1)
        mood_logs_1 = get_mood_logs(db_path, user_id_1)
        assert len(journals_1) == 0
        assert len(mood_logs_1) == 0
        
        # Save a journal for user 1
        analysis = JournalAnalysis(
            primary_emotion="anxiety",
            secondary_emotion="burnout",
            emotional_intensity=6,
            sentiment="negative",
            triggers=["mock tests"],
            thought_patterns=["guilt loop"],
            coping_strategies=["Take a 5 minute break"],
            risk_level=RiskLevel.moderate
        )
        
        journal_1 = JournalEntry(
            id="journal-u1-1",
            content="I feel anxious about student one's exams.",
            exam_context="exams",
            created_at=datetime.now(timezone.utc),
            analysis=analysis
        )
        save_journal(db_path, journal_1, user_id_1)
        
        # Save a journal for user 2
        journal_2 = JournalEntry(
            id="journal-u2-1",
            content="I feel confident about student two's preparation.",
            exam_context="exams",
            created_at=datetime.now(timezone.utc),
            analysis=analysis
        )
        save_journal(db_path, journal_2, user_id_2)
        
        # Verify user isolation on journals listing
        u1_journals = get_journals(db_path, user_id_1)
        u2_journals = get_journals(db_path, user_id_2)
        assert len(u1_journals) == 1
        assert u1_journals[0].id == "journal-u1-1"
        assert len(u2_journals) == 1
        assert u2_journals[0].id == "journal-u2-1"
        
        # Save a mood log for user 1
        mood_log_1 = MoodLog(
            id="mood-u1-1",
            mood_score=7,
            energy_level=6,
            sleep_hours=8.0,
            study_hours=6.5,
            stress_level=4,
            note="Feeling okay",
            created_at=datetime.now(timezone.utc)
        )
        save_mood_log(db_path, mood_log_1, user_id_1)
        
        # Retrieve and verify mood log isolation
        u1_moods = get_mood_logs(db_path, user_id_1)
        u2_moods = get_mood_logs(db_path, user_id_2)
        assert len(u1_moods) == 1
        assert u1_moods[0].id == "mood-u1-1"
        assert len(u2_moods) == 0
        
        # Verify counts are correct per user
        j_count_1, m_count_1 = get_counts(db_path, user_id_1)
        assert j_count_1 == 1
        assert m_count_1 == 1
        
        j_count_2, m_count_2 = get_counts(db_path, user_id_2)
        assert j_count_2 == 1
        assert m_count_2 == 0
        
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
