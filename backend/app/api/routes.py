from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.wellness import (
    ChatMessage,
    ChatResponse,
    JournalCreate,
    JournalEntry,
    MoodLog,
    MoodLogCreate,
    RiskLevel,
    UserCreate,
    UserLogin,
    Token,
    UserResponse
)
from app.services.dashboard import build_dashboard
from app.services.safety import CRISIS_MESSAGE, detect_crisis
from app.services.storage import store
from app.core.config import get_settings
from app.services.ai_analysis import get_gemini_chat_response
from app.services.auth import hash_password, verify_password, create_access_token, get_current_user
from app.services.database import get_user_by_username, save_user

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "mindmate-ai"}


# Authentication Endpoints
@router.post("/auth/signup", response_model=UserResponse)
def signup(payload: UserCreate) -> UserResponse:
    settings = get_settings()
    existing = get_user_by_username(settings.db_path, payload.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    user_id = str(uuid4())
    pw_hash = hash_password(payload.password)
    save_user(settings.db_path, user_id, payload.username, pw_hash)
    
    user = get_user_by_username(settings.db_path, payload.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering user"
        )
        
    created_at_dt = datetime.fromisoformat(user["created_at"])
    return UserResponse(
        id=user["id"],
        username=user["username"],
        created_at=created_at_dt
    )


@router.post("/auth/login", response_model=Token)
def login(payload: UserLogin) -> Token:
    settings = get_settings()
    user = get_user_by_username(settings.db_path, payload.username)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["id"], "username": user["username"]})
    return Token(access_token=access_token)


# Protected Wellness Endpoints
@router.post("/journals", response_model=JournalEntry)
def create_journal(payload: JournalCreate, current_user: dict = Depends(get_current_user)) -> JournalEntry:
    return store.add_journal(payload, user_id=current_user["id"])


@router.get("/journals", response_model=list[JournalEntry])
def list_journals(current_user: dict = Depends(get_current_user)) -> list[JournalEntry]:
    return store.get_recent_journals(user_id=current_user["id"])


@router.post("/mood-logs", response_model=MoodLog)
def create_mood_log(payload: MoodLogCreate, current_user: dict = Depends(get_current_user)) -> MoodLog:
    return store.add_mood_log(payload, user_id=current_user["id"])


@router.get("/mood-logs", response_model=list[MoodLog])
def list_mood_logs(current_user: dict = Depends(get_current_user)) -> list[MoodLog]:
    return store.get_recent_mood_logs(user_id=current_user["id"])


@router.get("/dashboard")
def dashboard(current_user: dict = Depends(get_current_user)):
    return build_dashboard(store, user_id=current_user["id"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatMessage, current_user: dict = Depends(get_current_user)) -> ChatResponse:
    # Deterministic crisis pre-check
    if detect_crisis(payload.message):
        return ChatResponse(
            response=CRISIS_MESSAGE,
            suggested_action="Contact emergency or trusted human support now.",
            risk_level=RiskLevel.crisis,
            crisis_detected=True,
        )

    # Try Gemini if enabled
    settings = get_settings()
    if settings.ai_provider == "gemini" and settings.gemini_api_key:
        res = get_gemini_chat_response(payload.message, settings.gemini_api_key)
        if res is not None:
            return res

    # Heuristic fallback response
    return ChatResponse(
        response=(
            "It sounds like you are carrying a lot. Let us shrink the next step: "
            "name one task you can finish in 25 minutes, then take a short reset."
        ),
        suggested_action="Try one focused 25-minute study block.",
        risk_level=RiskLevel.low,
    )
