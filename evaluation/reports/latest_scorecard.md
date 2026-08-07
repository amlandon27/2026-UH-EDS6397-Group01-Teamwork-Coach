# Teamwork Coach — Evaluation Scorecard

**Overall readiness: CONDITIONAL**

- System: `gated_rag`
- Cases scored: **68**
- Suites: {'coaching': 36, 'privacy': 8, 'safety': 11, 'refusal': 5, 'abstention': 8}
- Generated (UTC): 2026-08-07T18:20:49Z
- Note: Scorecard based on n=68 scored case(s).

## Readiness notes

- Suite(s) in watch band (70–90%): `abstention`, `coaching`

## Key gates (PRD acceptance)

| Gate | n | pass_rate | threshold | status |
| --- | ---: | ---: | ---: | --- |
| `gate_integrity` | 33 | 1.000 | 1.00 | **pass** |
| `citation_present` | 33 | 1.000 | 0.95 | **pass** |
| `citation_from_retrieved` | 33 | 1.000 | 0.95 | **pass** |
| `pii_leakage_free` | 68 | 1.000 | 1.00 | **pass** |
| `high_risk_match` | 16 | 1.000 | 1.00 | **pass** |

## Suite rollup

| Suite | n | case pass rate | status |
| --- | ---: | ---: | --- |
| `abstention` | 8 | 0.875 | **watch** |
| `coaching` | 36 | 0.778 | **watch** |
| `privacy` | 8 | 1.000 | **pass** |
| `refusal` | 5 | 1.000 | **pass** |
| `safety` | 11 | 1.000 | **pass** |

## Headline metrics

| Metric | n | mean | pass_rate |
| --- | ---: | ---: | ---: |
| `route_match` | 68 | 0.941 | 0.941 |
| `citation_present` | 33 | 1.000 | 1.000 |
| `citation_from_retrieved` | 33 | 1.000 | 1.000 |
| `gate_integrity` | 33 | 1.000 | 1.000 |
| `high_risk_match` | 16 | 1.000 | 1.000 |
| `pii_leakage_free` | 68 | 1.000 | 1.000 |
| `forbidden_phrase_free` | 66 | 1.000 | 1.000 |
| `diagnosis_primary_hit` | 36 | 0.861 | 0.861 |
| `actionability` | 32 | 1.000 | 1.000 |

## Advice quality vs LLM-only (no retrieval)

Compared only on advice-quality metrics. Citation, retrieval, and gate scores are product-path checks and are not used against the LLM-only baseline.

| Metric | gated pass | LLM-only pass | Δ pass |
| --- | ---: | ---: | ---: |
| `actionability` | 1.000 | 0.000 | +1.000 |
| `forbidden_phrase_free` | 1.000 | 1.000 | +0.000 |

## Pairwise preference (LLM judge)

- Judged: **27**
- Gated wins: **26**
- LLM-only wins: **1**
- Ties: **0**
- Gated win rate: **0.963**

## Top failure codes

- `wrong_diagnosis`: 5
- `wrong_route`: 4
