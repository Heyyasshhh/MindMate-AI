from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    low = "low"
    moderate = "moderate"
    high = "high"
    crisis = "crisis"


class MoodLogCreate(BaseModel):
    mood_score: int = Field(ge=1, le=10)
    energy_level: int | None = Field(default=None, ge=1, le=10)
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    study_hours: float | None = Field(default=None, ge=0, le=18)
    stress_level: int | None = Field(default=None, ge=1, le=10)
    note: str | None = Field(default=None, max_length=500)


class MoodLog(MoodLogCreate):
    id: str
    created_at: datetime


class JournalCreate(BaseModel):
    content: str = Field(min_length=10, max_length=4000)
    exam_context: str | None = Field(default=None, max_length=80)


class JournalAnalysis(BaseModel):
    primary_emotion: str
    secondary_emotion: str | None = None
    emotional_intensity: int = Field(ge=1, le=10)
    sentiment: str
    triggers: list[str]
    thought_patterns: list[str]
    coping_strategies: list[str]
    risk_level: RiskLevel
    crisis_detected: bool = False
    crisis_message: str | None = None


class JournalEntry(BaseModel):
    id: str
    content: str
    exam_context: str | None = None
    created_at: datetime
    analysis: JournalAnalysis


class ChatMessage(BaseModel):
    message: str = Field(min_length=1, max_length=1200)


class ChatResponse(BaseModel):
    response: str
    suggested_action: str | None = None
    risk_level: RiskLevel
    crisis_detected: bool = False


class DashboardSummary(BaseModel):
    mood_average: float
    journal_streak: int
    burnout_risk: RiskLevel
    wellness_progress: int = Field(ge=0, le=100)
    insights: list[str]
    recent_emotions: list[str]


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=6, max_length=100)


class UserLogin(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=6, max_length=100)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    username: str
    created_at: datetime

