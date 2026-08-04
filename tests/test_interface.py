"""Unit tests for student-facing interface helper functions."""

from types import SimpleNamespace

from interface.app import (
    _citation_target,
    _format_tag,
    _public_body,
)


def test_public_body_removes_fallback_internal_note():
    body = (
        "Public fallback guidance."
        "\n\nInternal routing note (not model advice):"
        "\n- Insufficient evidence."
    )

    assert (
        _public_body(
            route="fallback",
            body=body,
            has_resources=False,
        )
        == "Public fallback guidance."
    )


def test_public_body_removes_duplicate_escalation_resources():
    body = (
        "Please use the support resources below."
        "\n\nUniversity of Houston and related resources:"
        "\n- Resource one"
        "\n- Resource two"
    )

    assert (
        _public_body(
            route="escalation",
            body=body,
            has_resources=True,
        )
        == "Please use the support resources below."
    )


def test_public_body_preserves_coaching_response():
    body = "Validated coaching content."

    assert (
        _public_body(
            route="coaching",
            body=body,
            has_resources=False,
        )
        == body
    )


def test_public_body_preserves_escalation_body_without_resource_objects():
    body = (
        "Please use the support resources below."
        "\n\nUniversity of Houston and related resources:"
        "\n- Embedded resource"
    )

    assert (
        _public_body(
            route="escalation",
            body=body,
            has_resources=False,
        )
        == body
    )


def test_format_tag_converts_controlled_tag_to_readable_text():
    assert _format_tag("role_ambiguity") == "Role Ambiguity"
    assert _format_tag("communication_breakdown") == "Communication Breakdown"
    assert _format_tag(None) == ""


def test_citation_target_prefers_stored_url():
    citation = SimpleNamespace(
        url="https://example.edu/source",
        doi="10.1000/example",
    )

    assert _citation_target(citation) == "https://example.edu/source"


def test_citation_target_builds_clickable_doi_url():
    citation = SimpleNamespace(
        url=None,
        doi="10.1000/example",
    )

    assert _citation_target(citation) == "https://doi.org/10.1000/example"


def test_citation_target_preserves_existing_doi_url():
    citation = SimpleNamespace(
        url=None,
        doi="https://doi.org/10.1000/example",
    )

    assert _citation_target(citation) == "https://doi.org/10.1000/example"


def test_citation_target_returns_none_without_target():
    citation = SimpleNamespace(
        url=None,
        doi=None,
    )

    assert _citation_target(citation) is None
