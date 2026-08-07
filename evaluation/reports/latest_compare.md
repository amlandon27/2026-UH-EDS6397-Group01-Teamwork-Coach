# Advice Quality: Gated Coach vs LLM-only

- Cases: **68**
- Suites: {'coaching': 36, 'privacy': 8, 'safety': 11, 'refusal': 5, 'abstention': 8}

This comparison is limited to **advice-quality** metrics (`actionability`, `forbidden_phrase_free`, and optional `rubric_*`).
Retrieval, citation, and gate metrics are scored on the gated product path only.

Positive `Δ pass` means the gated coach scored higher on that advice metric.

| Metric | gated pass | LLM-only pass | Δ pass | gated mean | LLM-only mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| `actionability` | 1.000 | 0.000 | +1.000 | 1.000 | 0.000 |
| `forbidden_phrase_free` | 1.000 | 1.000 | +0.000 | 1.000 | 1.000 |

## Pairwise preference (LLM judge)

Forced choice: which answer better fits a cited, observational, proportionate teamwork coach (PRD-aligned).

- Judged: **27** / 31
- Gated wins: **26**
- LLM-only wins: **1**
- Ties: **0**
- Gated win rate: **0.963**

See `latest_preference.md` for per-case rationales.

## Advice-quality failure codes

### gated_rag
- `wrong_diagnosis`: 5
- `wrong_route`: 4

### LLM-only (no_rag)
- `weak_actionability`: 36
