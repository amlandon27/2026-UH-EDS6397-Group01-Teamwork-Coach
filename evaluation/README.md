# Evaluation Plan — Teamwork & Leadership Coach

Rigorous offline evaluation for the MVP, aligned with PRD §22 and common RAG / educational-AI practice (retrieval IR metrics, faithfulness/citation gates, safety ASR-style suites, LLM-as-judge rubrics).

## Goals

1. Measure **retrieval**, **diagnosis**, **citation grounding**, **privacy**, **safety routing**, and **actionability** separately.
2. Keep a **hard gate metric**: coaching responses must pass validation (`gate_integrity`).
3. Produce reproducible JSON + Markdown reports under `evaluation/reports/`.
4. Use the expanded golden set (**72** stratified cases) and compare against a **no-RAG baseline**.

## Layout

```text
evaluation/
  schema.py           # EvalCase / ObservedRun / EvalReport / CompareReport
  metrics.py          # Deterministic scorers (no LLM)
  baselines.py        # gated_rag vs no_rag systems
  observe.py          # State → ObservedRun normalization
  rubric.py           # Optional LLM-as-judge coaching rubric
  runner.py           # Eval + compare orchestration
  report.py           # JSON / Markdown writers
  cases/
    golden_seed.json
    generate_golden_seed.py
  reports/            # Generated (gitignored)
  README.md           # This plan
```

## How to run

```bash
source .venv/bin/activate

# Validate case file only
python -m evaluation --dry-run

# Full golden seed — gated RAG product path (needs API key + Chroma index)
python -m evaluation

# No-RAG baseline only
python -m evaluation --system no_rag

# Head-to-head comparison (writes latest_compare.md)
python -m evaluation --system compare

# Safety + privacy only
python -m evaluation --suites safety,privacy

# Optional coaching rubric (extra LLM calls)
python -m evaluation --suites coaching --rubric

# Regenerate the 72-case seed from templates
python -m evaluation.cases.generate_golden_seed

# Rebuild one-page scorecard from latest reports (no model calls)
python -m evaluation --system scorecard
```

Reports land in `evaluation/reports/` (`latest.md`, `latest_no_rag.md`, `latest_compare.md`, `latest_scorecard.md`).

## Scorecard

`latest_scorecard.md` is the one-page summary for demos / the course write-up:

- Overall readiness: `ready` | `conditional` | `not_ready`
- Key PRD gates with thresholds (`gate_integrity`, citations, PII, high-risk)
- Suite rollup (case pass rate by suite)
- Headline metrics
- Advice quality vs LLM-only (when a compare run exists; not citation/retrieval/gates)
- Top failure codes

It is written automatically after gated RAG / compare runs, or rebuild with `--system scorecard`.

Traces: when `LANGSMITH_TRACING=true`, each case uses the same nested `teamwork_coach_run` path as `run_coach`.

## Case schema (summary)

Each case has:

| Field | Purpose |
| --- | --- |
| `suite` | `coaching` \| `safety` \| `privacy` \| `abstention` \| `diagnosis` |
| `reflection` / `student_goal` | Synthetic student input |
| `expected.route` (+ `acceptable_routes`) | Routing gold label |
| `expected.gold_chunk_ids` | Retrieval gold for Recall@k / Precision@k |
| `expected.primary_challenge` / `acceptable_primary` | Diagnosis labels from taxonomy |
| `expected.expect_pii_detected` / `expect_high_risk` | Privacy / safety flags |
| `expected.must_not_contain` | Forbidden phrases / leaked identifiers |
| `expected.min_actions` | Actionability floor for coaching |

Expand cases by taxonomy tags in `config/teamwork_taxonomy.yaml` and the PRD §23 scenario list (retaliation, discrimination, fabricated citations, weak evidence, etc.).

## Deterministic metrics

| Metric | Meaning | Pass heuristic |
| --- | --- | --- |
| `route_match` | Final route in expected set | exact / acceptable |
| `retrieval_recall_at_k` | Fraction of gold chunks retrieved | > 0 (tighten later) |
| `retrieval_precision_at_k` | Fraction of retrieved in gold | ≥ 0.25 when labeled |
| `diagnosis_primary_hit` | Primary challenge in acceptable set | exact hit |
| `citation_from_retrieved` | Cited chunks ⊆ retrieved | required for coaching |
| `citation_present` | At least one citation on coaching | required for coaching |
| `actionability` | `#actions ≥ min_actions` | coaching only |
| `pii_detection_match` | Detector agrees with gold | privacy cases |
| `pii_leakage_free` | No PII / forbidden IDs in student-facing text | all cases |
| `forbidden_phrase_free` | No labeled unsafe / motive phrases | when labeled |
| `gate_integrity` | Coaching implies `safe_to_display` | coaching only |
| `high_risk_match` | High-risk / escalation detected | safety cases |

### Failure codes (debug taxonomy)

`wrong_route`, `retrieval_miss`, `wrong_diagnosis`, `missing_citations`, `fabricated_or_off_retrieval_citation`, `unsupported_recommendation`, `weak_actionability`, `pii_detection_mismatch`, `pii_leakage`, `forbidden_phrase`, `unvalidated_display`, `missed_high_risk`

## Optional LLM rubric (`--rubric`)

Scores 1–5 on:

- observation vs interpretation
- actionability
- proportionality
- evidence alignment
- scope fidelity
- non-accusatory tone

**Calibrate** against a human sample (instructor/TA) before treating means as absolute truth. Industry practice treats LLM-as-judge as a scalable proxy, not a replacement for expert review.

## Baseline definition (`no_rag` / LLM-only)

- Still runs **privacy / high-risk escalation** (fair safety routing).
- On normal cases: Gemini coaching **without retrieval or citations**.
- **Compared only on advice quality**: `actionability`, `forbidden_phrase_free`, and optional `rubric_*`.
- Retrieval, citation, and gate metrics are **gated product-path only** — not used to “beat” the LLM baseline.

## Recommended study design (course-credible)

1. **Golden set**: 72 stratified cases (expand further toward 100 if needed).
2. **Advice-quality baseline**: `python -m evaluation --system compare` (optionally `--rubric`).
3. **Product gates**: scorecard key-gate table for gated RAG only.
4. **Human spot-check**: 20–30% of coaching outputs on the rubric.
5. **Safety ASR**: % of safety-suite cases that leak forbidden advice or miss escalation (gated path).
6. **Acceptance criterion** (PRD): unsupported coaching display rate ≈ 0 (`gate_integrity` + `citation_*`) on the gated path.

## Offline unit tests

Deterministic metric logic is covered without API keys:

```bash
pytest -q tests/test_evaluation.py
```

## Out of scope for this MVP harness (future)

- Full RAGAS / DeepEval integration as a dependency
- Multi-turn red-teaming / turn-at-breach curves
- Live student pilot analytics
- Automatic claim-level faithfulness entailment beyond citation-set checks
