"""Run golden-set evaluation against coach and baseline systems."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from evaluation.baselines import SystemName, invoke_system
from evaluation.metrics import aggregate_results, count_failure_codes, score_case
from evaluation.report import write_compare_report, write_report
from evaluation.schema import (
    CaseResult,
    CompareReport,
    EvalCase,
    EvalCaseFile,
    EvalReport,
    SystemCompareRow,
)
from evaluation.scorecard import build_scorecard, write_scorecard

ROOT = Path(__file__).resolve().parent
DEFAULT_CASES = ROOT / "cases" / "golden_seed.json"
DEFAULT_REPORT_DIR = ROOT / "reports"


def load_cases(path: Path | str) -> list[EvalCase]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return EvalCaseFile.model_validate(data).cases


def filter_cases(
    cases: Iterable[EvalCase],
    *,
    suites: Optional[set[str]] = None,
    case_ids: Optional[set[str]] = None,
) -> list[EvalCase]:
    selected: list[EvalCase] = []
    for case in cases:
        if suites and case.suite not in suites:
            continue
        if case_ids and case.case_id not in case_ids:
            continue
        selected.append(case)
    return selected


def run_eval(
    cases: list[EvalCase],
    *,
    system: SystemName = "gated_rag",
    with_rubric: bool = False,
    report_dir: Path | str = DEFAULT_REPORT_DIR,
    write: bool = True,
) -> EvalReport:
    """Execute cases on one system, score, optionally LLM-judge, write report."""
    results: list[CaseResult] = []
    total = len(cases)
    print(f"\n[{system}] running {total} case(s)...", flush=True)
    for index, case in enumerate(cases, start=1):
        print(
            f"[{system}] {index}/{total} {case.case_id} [{case.suite}] ...",
            flush=True,
        )
        try:
            observed = invoke_system(case, system)
        except Exception as exc:  # noqa: BLE001
            from services.llm_service import GeminiQuotaExceeded

            if isinstance(exc, GeminiQuotaExceeded) or "RESOURCE_EXHAUSTED" in str(exc):
                print(
                    f"\n[{system}] STOPPED: Gemini quota exceeded at case "
                    f"{index}/{total} ({case.case_id}).\n{exc}",
                    flush=True,
                )
                raise
            print(f"[{system}] {index}/{total} EXCEPTION: {exc}", flush=True)
            from evaluation.schema import ObservedRun

            observed = ObservedRun(error=str(exc))
        result = score_case(case, observed, system=system)
        if with_rubric:
            from evaluation.rubric import RUBRIC_DIMENSIONS, judge_coaching_quality
            from evaluation.schema import MetricScore

            try:
                result.rubric = judge_coaching_quality(case, observed)
                for dim in RUBRIC_DIMENSIONS:
                    value = result.rubric.get(dim)
                    if isinstance(value, (int, float)):
                        score = float(value) / 5.0
                        result.metrics.append(
                            MetricScore(
                                name=f"rubric_{dim}",
                                value=score,
                                passed=float(value) >= 4.0,
                                detail=f"rubric={value}/5",
                            )
                        )
            except Exception as exc:  # noqa: BLE001
                result.rubric = {"error": str(exc)}
        status = "ok" if not result.failure_codes and not observed.error else (
            f"error={observed.error}" if observed.error else f"fail={result.failure_codes}"
        )
        print(
            f"[{system}] {index}/{total} done route={observed.route or '—'} "
            f"latency={observed.latency_ms:.0f}ms {status}",
            flush=True,
        )
        results.append(result)

    suite_counts: dict[str, int] = {}
    for case in cases:
        suite_counts[case.suite] = suite_counts.get(case.suite, 0) + 1

    report = EvalReport(
        system=system,
        case_count=len(results),
        suite_counts=suite_counts,
        aggregates=aggregate_results(results),
        failure_code_counts=count_failure_codes(results),
        cases=results,
    )
    if write:
        write_report(report, Path(report_dir), prefix=f"eval_{system}")
        if system == "gated_rag":
            write_scorecard(build_scorecard(report), Path(report_dir))
    return report


def run_compare(
    cases: list[EvalCase],
    *,
    with_rubric: bool = False,
    report_dir: Path | str = DEFAULT_REPORT_DIR,
) -> CompareReport:
    """Run gated RAG vs no-RAG baseline on the same cases."""
    print(
        f"\nCompare mode: {len(cases)} case(s) × 2 systems "
        "(gated_rag first, then LLM-only). This can take a long time.",
        flush=True,
    )
    gated = run_eval(
        cases,
        system="gated_rag",
        with_rubric=with_rubric,
        report_dir=report_dir,
        write=True,
    )
    baseline = run_eval(
        cases,
        system="no_rag",
        with_rubric=with_rubric,
        report_dir=report_dir,
        write=True,
    )
    compare = CompareReport(
        case_count=len(cases),
        suite_counts=dict(gated.suite_counts),
        rows=_compare_rows(gated, baseline),
        gated_rag=gated,
        no_rag=baseline,
    )
    out = Path(report_dir)
    write_compare_report(compare, out)
    write_scorecard(build_scorecard(gated, compare=compare), out)
    return compare


def _compare_rows(gated: EvalReport, baseline: EvalReport) -> list[SystemCompareRow]:
    """Compare only advice-quality metrics (fair LLM-only baseline)."""
    from evaluation.metrics import ADVICE_QUALITY_METRICS

    gated_map = {a.name: a for a in gated.aggregates}
    base_map = {a.name: a for a in baseline.aggregates}
    names = sorted(
        name
        for name in (set(gated_map) | set(base_map))
        if name in ADVICE_QUALITY_METRICS or name.startswith("rubric_")
    )
    rows: list[SystemCompareRow] = []
    for name in names:
        g = gated_map.get(name)
        b = base_map.get(name)
        g_rate = g.pass_rate if g else None
        b_rate = b.pass_rate if b else None
        delta = None
        if g_rate is not None and b_rate is not None:
            delta = g_rate - b_rate
        rows.append(
            SystemCompareRow(
                metric=name,
                gated_rag_mean=g.mean if g else None,
                gated_rag_pass_rate=g_rate,
                no_rag_mean=b.mean if b else None,
                no_rag_pass_rate=b_rate,
                delta_pass_rate=delta,
            )
        )
    return rows
