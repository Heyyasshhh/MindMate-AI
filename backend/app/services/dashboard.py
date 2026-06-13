from statistics import mean
from app.models.wellness import DashboardSummary, RiskLevel


def build_dashboard(store, user_id: str) -> DashboardSummary:
    recent_mood_logs = store.get_recent_mood_logs(user_id, 7)
    recent_journals = store.get_recent_journals(user_id, 7)
    
    mood_scores = [log.mood_score for log in recent_mood_logs]
    risk_values = [entry.analysis.risk_level for entry in recent_journals]
    recent_emotions = [entry.analysis.primary_emotion for entry in recent_journals[:5]]
    burnout = _highest_risk(risk_values, mood_scores)

    insights = []
    if mood_scores:
        insights.append(f"Your recent average mood is {mean(mood_scores):.1f}/10.")
    if recent_emotions:
        common = max(set(recent_emotions), key=recent_emotions.count)
        insights.append(f"Most frequent recent emotion: {common}.")
    if not insights:
        insights.append("Add a journal entry and mood log to unlock weekly insights.")

    journal_count, mood_count = store.get_counts(user_id)
    progress = min(100, mood_count * 8 + journal_count * 10)
    return DashboardSummary(
        mood_average=round(mean(mood_scores), 1) if mood_scores else 0,
        journal_streak=min(7, journal_count),
        burnout_risk=burnout,
        wellness_progress=progress,
        insights=insights,
        recent_emotions=recent_emotions,
    )


def _highest_risk(risks: list[RiskLevel], mood_scores: list[int]) -> RiskLevel:
    if RiskLevel.crisis in risks:
        return RiskLevel.crisis
    if RiskLevel.high in risks or (mood_scores and mean(mood_scores) <= 4):
        return RiskLevel.high
    if RiskLevel.moderate in risks or (mood_scores and mean(mood_scores) <= 6):
        return RiskLevel.moderate
    return RiskLevel.low
