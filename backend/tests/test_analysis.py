from app.services.ai_analysis import analyze_journal


def test_journal_analysis_detects_peer_comparison() -> None:
    result = analyze_journal("Everyone else is ahead. I feel anxious and guilty after my mock test.")

    assert result.primary_emotion == "anxiety"
    assert "peer comparison" in result.triggers
    assert result.risk_level in {"moderate", "high"}


def test_journal_analysis_detects_crisis_language() -> None:
    result = analyze_journal("Life feels pointless and I do not want to continue.")

    assert result.crisis_detected is True
    assert result.risk_level == "crisis"
