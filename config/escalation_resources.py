"""Verified University of Houston escalation resources (config, not model memory)."""

from __future__ import annotations

ESCALATION_INTRO = (
    "This situation appears to need human support rather than ordinary teamwork coaching. "
    "The system will not generate standard coaching advice for this reflection. "
    "Please use the resources below. If you or someone else may be in immediate danger, "
    "call 911 or campus emergency services now."
)

ESCALATION_RESOURCES: list[dict[str, str]] = [
    {
        "name": "UH Counseling and Psychological Services (CAPS)",
        "detail": "Confidential mental-health support for UH students.",
        "url": "https://www.uh.edu/caps/",
        "phone": "713-743-5454",
    },
    {
        "name": "UH Title IX / Equal Opportunity Services",
        "detail": "Support and reporting pathways related to discrimination, harassment, and sexual misconduct.",
        "url": "https://www.uh.edu/equal-opportunity/",
        "phone": "713-743-8835",
    },
    {
        "name": "UH Dean of Students",
        "detail": "Student support, conduct concerns, and guidance on university processes.",
        "url": "https://www.uh.edu/dos/",
        "phone": "",
    },
    {
        "name": "UH Police Department (non-emergency)",
        "detail": "Campus safety support. For emergencies, call 911.",
        "url": "https://www.uh.edu/police/",
        "phone": "713-743-3333",
    },
    {
        "name": "National Suicide & Crisis Lifeline",
        "detail": "24/7 support for people in emotional distress or suicidal crisis.",
        "url": "https://988lifeline.org/",
        "phone": "988",
    },
]

SAFE_FALLBACK_MESSAGE = (
    "I could not produce a validated, evidence-grounded coaching response for this reflection. "
    "That may be because the evidence was insufficient, the draft did not pass safety checks, "
    "or the situation is outside ordinary teamwork coaching. "
    "Consider restating observable behaviors (what happened, when, and who was involved without names), "
    "or talking with a teammate, instructor, or advisor."
)
