"""Corpus and contract smoke tests."""

import json
from pathlib import Path

from contract import AgentState, TeamworkDiagnosis


ROOT = Path(__file__).resolve().parents[1]


def test_corpus_chunk_source_ids_resolve():
    sources = {
        s["source_id"]
        for s in json.loads((ROOT / "corpus/sources/sources.json").read_text())
    }
    chunks = json.loads((ROOT / "corpus/chunks/chunks.json").read_text())
    assert len(chunks) >= 8
    for chunk in chunks:
        assert chunk["source_id"] in sources
        assert chunk["human_reviewed"] is True


def test_agent_state_defaults():
    state = AgentState(raw_input="hello")
    assert state.regeneration_count == 0
    assert state.safe_to_display is False
    diagnosis = TeamworkDiagnosis(primary_challenge="role_ambiguity")
    assert diagnosis.secondary_challenges == []
