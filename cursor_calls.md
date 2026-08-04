# Cursor Calls — Key Decisions Log

Decisions made while building the MVP. Keep entries short and dated.

## 2026-08-03 — Stack lock (pre-build)

| Decision | Choice | Rationale |
| --- | --- | --- |
| LLM | Google Gemini Flash (`gemini-3.5-flash`) | Free tier, strong structured output, LangChain support; 2.5 Flash unavailable to new API users |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Local, free, fast enough for small corpus |
| Vector store | ChromaDB (local) | Simple local persistence, no hosted infra |
| Interface | Streamlit | Fastest Python demo UI |
| Corpus (MVP) | Hand-built tagged chunks | Ship end-to-end now; replace with ingestion later |
| PII user flow | Automatic redaction before downstream processing | Simplest path that meets PRD privacy rule |
| LangSmith | Off by default; when enabled, one nested sanitized trace per `run_coach` | Privacy-preserving observability for demos/debug |
| Citation style | APA 7 | Matches PRD proposal |
| Repair | One controlled repair attempt, then fallback | Matches PRD |
| High-risk detection | Keyword/heuristic gate before LLM coaching | Deterministic, cheap, fails safe |
| Retrieval sufficiency | Require ≥1 retrieved chunk above similarity threshold | Simple abstain rule |
| Project layout | PRD §24 structure at repo root | Keep teammates aligned with PRD |

## Build notes

- Prefer programmatic guardrails where possible; use LLM for diagnosis/advice/validation only.
- No long-term memory or auth in MVP.
- Session-only: no persistent student profiles.

## 2026-08-03 — Implementation choices during build

| Decision | Choice | Rationale |
| --- | --- | --- |
| PII user flow | Auto-redact, continue | Simplest PRD-compliant path |
| High-risk gate | Keyword heuristics before diagnosis | Deterministic fail-safe; no LLM needed |
| Validation | Programmatic checks (citations, PII, prohibited patterns, motive, overconfidence) | Reliable; LLM drafts only |
| Diagnosis+retrieval | One LangGraph node | Matches PRD MVP note |
| Repair loop | validation → repair_increment → advice (max 1) | Matches PRD |
| Corpus size | 10 hand-tagged chunks / 5 sources | Enough to demo retrieval + citations |
| Index build | `python -m ingestion.build_index` | Explicit rebuild step |
| Placeholder ingestion modules | Present but `NotImplementedError` | Preserve PRD layout for later swap |
| LLM model pin | Switched default from `gemini-2.5-flash` to `gemini-3.5-flash` | API returned 404 for new users on 2.5 Flash |
| Retrieval min score | Lowered default to `0.05` | Chroma relevance scores often land well below 0.25 for short reflections |

## 2026-08-03 — LangSmith nested tracing

| Decision | Choice | Rationale |
| --- | --- | --- |
| Observability | LangSmith via `services/tracing_service.py` | One nested trace per coach run (graph + LLM + retrieval) |
| Default | `LANGSMITH_TRACING=false` | No key required for local/tests |
| Privacy | Omit `raw_input`/`reflection`; PII-redact other strings | Matches PRD telemetry rule |
| Wiring | `run_with_tracing` + `@traceable` root + node/LLM/retriever spans | Full end-to-end chain in one link |
