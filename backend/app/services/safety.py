from app.models.wellness import RiskLevel


CRISIS_TERMS = [
    "don't want to continue",
    "do not want to continue",
    "life feels pointless",
    "end my life",
    "suicide",
    "kill myself",
    "self harm",
    "hurt myself",
]

CRISIS_MESSAGE = (
    "I am really sorry you are feeling this way. Please contact a trusted adult, "
    "local emergency services, or a mental health crisis helpline right now. "
    "If you are in immediate danger, call your local emergency number."
)


def detect_crisis(text: str) -> bool:
    normalized = text.lower()
    return any(term in normalized for term in CRISIS_TERMS)


def safety_level(text: str) -> RiskLevel:
    return RiskLevel.crisis if detect_crisis(text) else RiskLevel.low
