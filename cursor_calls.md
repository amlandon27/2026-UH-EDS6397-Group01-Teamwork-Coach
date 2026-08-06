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

## 2026-08-04 — LLM provider switch (Gemini quota)

| Decision | Choice | Rationale |
| --- | --- | --- |
| Default LLM | Ollama `llama3.1:8b` via `LLM_PROVIDER=ollama` | Gemini free-tier 429 RESOURCE_EXHAUSTED |
| Fallback | Auto Ollama on Gemini quota errors | Keep demos working without billing |
| Config | `OLLAMA_HOST` / `OLLAMA_MODEL` in settings | Same local stack as corpus builder |
| Quota error type | `GeminiQuotaExceeded` raised for Gemini 429 | Evaluation runner can stop cleanly |

## 2026-08-04 — Evaluation harness (teammate merge)

| Decision | Choice | Rationale |
| --- | --- | --- |
| Eval layout | `evaluation/` package + `cases/golden_seed.json` | Matches PRD tree; keeps scoring separate from app runtime |
| Metrics core | Deterministic first (route, retrieval, citations, PII, gates) | Reliable CI; no judge drift |
| LLM rubric | Optional `--rubric` only | Costly; needs human calibration |
| State capture | Invoke full LangGraph state (not FinalResponse-only) | Needed for retrieval + validation metrics |
| Seed size | 84 stratified synthetic cases (generator script) | Course-credible coverage across taxonomy + safety + gap scenarios |
| Baseline | LLM-only advice-quality compare (`actionability`, phrases, optional rubric) | Avoid fake wins on citation/retrieval/gates |
| Scorecard | `latest_scorecard.md` with readiness + gates + suite rollup | One-page stakeholder summary; rebuild with `--system scorecard` |
| Active corpus for eval | Instructor-promoted builder export under `corpus/` | No fixed `gold_chunk_ids`; IR metrics retired |
| Builder dump | Keep under `corpus/expanded_from_builder/` | Promote after review without breaking eval |

## 2026-08-05 — Active corpus = builder export

| Decision | Choice | Rationale |
| --- | --- | --- |
| Active corpus | Builder export (353 chunks / 22 sources) in `corpus/` | Placeholder MVP corpus retired; builder drops into the corpus the coach uses |
| Parking folder | Removed `corpus/expanded_from_builder/` | Single source of truth; promote = replace + `build_index` |
| Eval gold IDs | Deferred update | Retrieval IR metrics need relabel; other suites still valid |
| `human_reviewed` | Many builder chunks still `false` | Contract test checks field type only until review catches up |

## 2026-08-04 — Knowledge Corpus Builder

| Decision | Choice | Rationale |
| --- | --- | --- |
| Placement | Standalone Streamlit under `Knowledge_Corpus_Builder/` | Keep builder separate from coach runtime |
| Conversion | Docling for pdf/pptx/docx/txt/md/html/images | One converter for all day-one formats |
| Markdown repair | Ollama `llama3.1:8b` local | Strip ads/noise without cloud dependency |
| Tag suggestion | Same Ollama model + taxonomy filter | Local structured tags; invalid terms dropped |
| Chunking | Structure-based (headings/slides/paragraphs) | Matches PRD meaning-oriented chunking |
| Clustering | MiniLM embeddings + agglomerative + near-dupe merge | Merge/dedupe/organize review batches |
| Human review | Batch by source/cluster; approve/reject/needs_rewrite | PRD requires human approval path |
| Export | `Corpus_Output` + `*_mvp.json` copy-compatible schema | Manual handoff into `corpus/` after evals |
| MVP corpus | Keep until evals | Do not auto-overwrite coach evidence |

## 2026-08-03 — LangSmith nested tracing

| Decision | Choice | Rationale |
| --- | --- | --- |
| Observability | LangSmith via `services/tracing_service.py` | One nested trace per coach run (graph + LLM + retrieval) |
| Default | `LANGSMITH_TRACING=false` | No key required for local/tests |
| Privacy | Omit `raw_input`/`reflection`; PII-redact other strings | Matches PRD telemetry rule |
| Wiring | `run_with_tracing` + `@traceable` root + node/LLM/retriever spans | Full end-to-end chain in one link |
