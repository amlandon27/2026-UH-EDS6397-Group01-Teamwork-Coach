"""Unit tests for PII detection/redaction."""

from guardrails.pii_redaction import contains_pii, detect_pii, redact_pii


def test_redacts_email_and_phone():
    text = "Email me at jane.doe@uh.edu or call 713-555-0199 about the project."
    redacted, spans = redact_pii(text)
    labels = {s.label for s in spans}
    assert "email" in labels
    assert "phone" in labels
    assert "jane.doe@uh.edu" not in redacted
    assert "713-555-0199" not in redacted
    assert "[EMAIL]" in redacted
    assert "[PHONE]" in redacted


def test_redacts_named_teammate():
    text = "My teammate Jordan Smith missed the CAD handoff again."
    redacted, spans = redact_pii(text)
    assert any(s.label == "person_name" for s in spans)
    assert "Jordan Smith" not in redacted


def test_clean_reflection_has_no_pii():
    text = (
        "Our team keeps missing intermediate checkpoints and task ownership is unclear."
    )
    assert contains_pii(text) is False
    assert detect_pii(text) == []
