"""Tests for Ollama/Docling repair artifact stripping and clean triage."""

from Knowledge_Corpus_Builder.pipeline.clean_and_promote import reject_reason
from Knowledge_Corpus_Builder.pipeline.markdown_repair import strip_repair_artifacts
from Knowledge_Corpus_Builder.schemas.models import ChunkRecord


def test_strip_leading_cleaned_markdown_preamble():
    raw = (
        "## Preamble\n\n"
        "Here is the cleaned markdown:\n\n"
        "## 8 Essential Leadership Communication Skills\n\n"
        "By Lauren Landry on November 14, 2019\n"
    )
    cleaned = strip_repair_artifacts(raw)
    assert "Here is the cleaned markdown" not in cleaned
    assert "## Preamble" not in cleaned
    assert "8 Essential Leadership Communication Skills" in cleaned


def test_strip_note_removed_block():
    raw = (
        "## Data Analysis\n\n"
        "Note: I removed the following sections as they were not relevant:\n\n"
        "* Shazib Vijlee's biography\n"
        "* Figure 1 (image)\n\n"
        "I also fixed broken headings and list structure where possible.\n\n"
        "Here is the cleaned markdown:\n\n"
        "Students reported clearer decision criteria after the exercise.\n"
    )
    cleaned = strip_repair_artifacts(raw)
    assert "Note: I removed" not in cleaned
    assert "Here is the cleaned markdown" not in cleaned
    assert "Shazib" not in cleaned
    assert "Students reported clearer decision criteria" in cleaned
    assert "## Data Analysis" in cleaned


def test_strip_leaves_clean_text_unchanged():
    raw = (
        "## Psychological safety\n\n"
        "Teams perform better when members can take interpersonal risks.\n"
    )
    assert strip_repair_artifacts(raw) == raw.strip()


def test_reject_too_short_after_clean():
    chunk = ChunkRecord(
        chunk_id="chk_x",
        source_id="src_x",
        text="Too short.",
        challenge_tags=["accountability"],
    )
    assert reject_reason(chunk, min_chars=120) == "too_short"


def test_approve_substantive_tagged_chunk():
    chunk = ChunkRecord(
        chunk_id="chk_ok",
        source_id="src_x",
        text=(
            "## Accountability\n\n"
            "Named owners and midpoint checkpoints reduce dropped deliverables "
            "on student engineering teams when roles stay visible across weeks."
        ),
        challenge_tags=["accountability"],
        signal_tags=["missed_deadline"],
    )
    assert reject_reason(chunk, min_chars=120) is None
