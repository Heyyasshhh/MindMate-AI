import json
import logging
from collections import Counter
import httpx
from app.models.wellness import JournalAnalysis, RiskLevel, ChatResponse
from app.services.safety import CRISIS_MESSAGE, detect_crisis
from app.core.config import get_settings

logger = logging.getLogger("mindmate-ai")

EMOTION_KEYWORDS = {
    "anxiety": ["anxious", "panic", "worried", "scared", "nervous", "fear"],
    "burnout": ["tired", "exhausted", "drained", "burnout", "overwhelmed"],
    "self-doubt": ["guilty", "behind", "failure", "incapable", "not enough"],
    "low motivation": ["quit", "procrastinate", "stuck", "unmotivated"],
    "sadness": ["sad", "lonely", "hopeless", "cry", "empty"],
}

TRIGGER_KEYWORDS = {
    "mock tests": ["mock", "test", "score", "rank"],
    "peer comparison": ["everyone else", "friends", "peers", "comparison", "ahead"],
    "parental pressure": ["parents", "family", "expectations"],
    "sleep disruption": ["sleep", "insomnia", "late night"],
    "study consistency": ["hours", "studied", "syllabus", "revision"],
}


def analyze_journal(content: str) -> JournalAnalysis:
    # Deterministic safety pre-check
    if detect_crisis(content):
        return JournalAnalysis(
            primary_emotion="crisis",
            secondary_emotion=None,
            emotional_intensity=10,
            sentiment="negative",
            triggers=["extreme distress"],
            thought_patterns=["harmful ideation"],
            coping_strategies=["Pause the app and contact immediate human support.", "Move near a trusted person if possible."],
            risk_level=RiskLevel.crisis,
            crisis_detected=True,
            crisis_message=CRISIS_MESSAGE,
        )

    # Check for Gemini provider
    settings = get_settings()
    if settings.ai_provider == "gemini" and settings.gemini_api_key:
        result = _analyze_with_gemini(content, settings.gemini_api_key)
        if result is not None:
            return result

    # Fallback/Default Heuristic analysis
    return _analyze_heuristic(content)


def _analyze_with_gemini(content: str, api_key: str) -> JournalAnalysis | None:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = (
        "Analyze the following student journal entry for emotional wellness. "
        "The student is preparing for a high-stakes exam. Identify emotions, triggers, thought patterns, and coping strategies. "
        "Return a JSON object conforming exactly to the following JSON schema:\n"
        "{\n"
        "  \"primary_emotion\": \"string (anxiety, burnout, self-doubt, low motivation, sadness, or reflective)\",\n"
        "  \"secondary_emotion\": \"string or null\",\n"
        "  \"emotional_intensity\": \"integer between 1 and 10\",\n"
        "  \"sentiment\": \"string (positive, negative, or neutral)\",\n"
        "  \"triggers\": [\"list of strings describing triggers, e.g., 'mock tests', 'peer comparison', 'parental pressure', 'sleep disruption', 'study consistency'\u0022],\n"
        "  \"thought_patterns\": [\"list of strings describing negative thinking styles, e.g., 'comparison-driven self-talk', 'all-or-nothing thinking', 'guilt loop'\u0022],\n"
        "  \"coping_strategies\": [\"list of 2-3 specific, short, actionable suggestions tailored to their state\"]\n"
        "}\n\n"
        f"Journal Entry:\n{content}"
    )
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            text_response = data["candidates"][0]["content"]["parts"][0]["text"]
            analysis_dict = json.loads(text_response.strip())
            
            intensity = int(analysis_dict.get("emotional_intensity", 5))
            primary = str(analysis_dict.get("primary_emotion", "reflective")).lower()
            
            # Map risk level
            if primary == "burnout" or intensity >= 7:
                risk = RiskLevel.high
            elif intensity >= 5 or primary in {"anxiety", "self-doubt"}:
                risk = RiskLevel.moderate
            else:
                risk = RiskLevel.low
                
            return JournalAnalysis(
                primary_emotion=primary,
                secondary_emotion=analysis_dict.get("secondary_emotion"),
                emotional_intensity=intensity,
                sentiment=analysis_dict.get("sentiment", "neutral"),
                triggers=analysis_dict.get("triggers") or ["daily study pressure"],
                thought_patterns=analysis_dict.get("thought_patterns") or ["no strong negative pattern detected"],
                coping_strategies=analysis_dict.get("coping_strategies") or ["Take a slow deep breath."],
                risk_level=risk,
                crisis_detected=False,
                crisis_message=None
            )
    except Exception as e:
        logger.warning(f"Gemini journal analysis failed, falling back to heuristic: {e}")
        return None


def _analyze_heuristic(content: str) -> JournalAnalysis:
    text = content.lower()
    emotion_scores = Counter()

    for emotion, keywords in EMOTION_KEYWORDS.items():
        emotion_scores[emotion] = sum(1 for word in keywords if word in text)

    ranked = [item for item in emotion_scores.most_common() if item[1] > 0]
    primary = ranked[0][0] if ranked else "reflective"
    secondary = ranked[1][0] if len(ranked) > 1 else None

    triggers = [
        label for label, keywords in TRIGGER_KEYWORDS.items() if any(word in text for word in keywords)
    ]
    thought_patterns = []
    if any(term in text for term in ["everyone else", "behind", "not enough"]):
        thought_patterns.append("comparison-driven self-talk")
    if any(term in text for term in ["always", "never", "failure"]):
        thought_patterns.append("all-or-nothing thinking")
    if any(term in text for term in ["guilty", "should have"]):
        thought_patterns.append("guilt loop")

    intensity = min(10, 3 + sum(score for _, score in ranked) + len(thought_patterns))
    if primary == "burnout" or intensity >= 7:
        risk = RiskLevel.high
    elif intensity >= 5 or primary in {"anxiety", "self-doubt"}:
        risk = RiskLevel.moderate
    else:
        risk = RiskLevel.low

    return JournalAnalysis(
        primary_emotion=primary,
        secondary_emotion=secondary,
        emotional_intensity=intensity,
        sentiment="negative" if ranked else "neutral",
        triggers=triggers or ["daily study pressure"],
        thought_patterns=thought_patterns or ["no strong negative pattern detected"],
        coping_strategies=_coping_strategies(primary, risk),
        risk_level=risk,
        crisis_detected=False,
        crisis_message=None,
    )


def _coping_strategies(primary: str, risk: RiskLevel) -> list[str]:
    strategies = {
        "anxiety": ["Try 4-7-8 breathing for two minutes.", "Write the next single study action, not the whole backlog."],
        "burnout": ["Take a 20-minute restorative break without screens.", "Reduce the next session to one focused 25-minute block."],
        "self-doubt": ["List three completed tasks from today.", "Replace rank comparison with one personal progress metric."],
        "low motivation": ["Start with the easiest 10-minute task.", "Use a timer and stop when it rings."],
        "sadness": ["Send one honest message to a trusted person.", "Do a brief self-compassion reflection."],
    }
    return strategies.get(primary, ["Journal one thing that felt difficult and one thing you handled."])


def get_gemini_chat_response(message: str, api_key: str) -> ChatResponse | None:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = (
        "You are MindMate AI, a supportive, empathetic emotional wellness companion for a student preparing for competitive/board exams. "
        "Provide a gentle, non-clinical response (max 2-3 sentences) to the student. Help them break down their stress/procrastination into tiny steps. "
        "Also provide a suggested actionable next-step, and classify the emotional risk level ('low', 'moderate', or 'high'). "
        "Return a JSON object conforming exactly to this schema:\n"
        "{\n"
        "  \"response\": \"string\",\n"
        "  \"suggested_action\": \"string or null\",\n"
        "  \"risk_level\": \"low | moderate | high\"\n"
        "}\n\n"
        f"Student Message: {message}"
    )
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            text_response = data["candidates"][0]["content"]["parts"][0]["text"]
            chat_dict = json.loads(text_response.strip())
            
            return ChatResponse(
                response=chat_dict.get("response", "I hear you. Let's take a deep breath together."),
                suggested_action=chat_dict.get("suggested_action"),
                risk_level=RiskLevel(chat_dict.get("risk_level", "low")),
                crisis_detected=False
            )
    except Exception as e:
        logger.warning(f"Gemini companion chat failed, falling back: {e}")
        return None
