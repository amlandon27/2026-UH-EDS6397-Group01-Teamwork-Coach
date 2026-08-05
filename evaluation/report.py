"""Serialize evaluation and comparison reports to JSON and Markdown."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from evaluation.schema import CompareReport, EvalReport

_ADVICE_FAILURE_CODES = frozenset({"weak_actionability", "forbidden_phrase"})


def write_report(
    report: EvalReport,
    report_dir: Path,
    *,
    prefix: str = "eval_report",
) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = report_dir / f"{prefix}_{stamp}.json"
    md_path = report_dir / f"{prefix}_{stamp}.md"
    latest_json = report_dir / f"latest_{report.system}.json"
    latest_md = report_dir / f"latest_{report.system}.md"
    # Keep generic latest aliases for the default gated system.
    payload = report.model_dump()
    json_text = json.dumps(payload, indent=2)
    md_text = render_markdown(report)

    json_path.write_text(json_text, encoding="utf-8")
    md_path.write_text(md_text, encoding="utf-8")
    latest_json.write_text(json_text, encoding="utf-8")
    latest_md.write_text(md_text, encoding="utf-8")
    if report.system == "gated_rag":
        (report_dir / "latest.json").write_text(json_text, encoding="utf-8")
        (report_dir / "latest.md").write_text(md_text, encoding="utf-8")
    return json_path, md_path


def write_compare_report(
    report: CompareReport, report_dir: Path
) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = report_dir / f"compare_gated_vs_norag_{stamp}.json"
    md_path = report_dir / f"compare_gated_vs_norag_{stamp}.md"
    latest_json = report_dir / "latest_compare.json"
    latest_md = report_dir / "latest_compare.md"

    # Avoid nesting full case dumps twice in the compare JSON blob size explosion:
    # keep aggregates + rows; attach slim case failure summaries.
    payload = {
        "version": report.version,
        "case_count": report.case_count,
        "suite_counts": report.suite_counts,
        "rows": [r.model_dump() for r in report.rows],
        "gated_rag": {
            "system": report.gated_rag.system,
            "case_count": report.gated_rag.case_count,
            "aggregates": [a.model_dump() for a in report.gated_rag.aggregates],
            "failure_code_counts": report.gated_rag.failure_code_counts,
        },
        "no_rag": {
            "system": report.no_rag.system,
            "case_count": report.no_rag.case_count,
            "aggregates": [
                a.model_dump()
                for a in report.no_rag.aggregates
                if a.name in {"actionability", "forbidden_phrase_free"}
                or a.name.startswith("rubric_")
            ],
            "failure_code_counts": {
                k: v
                for k, v in report.no_rag.failure_code_counts.items()
                if k in _ADVICE_FAILURE_CODES
            },
        },
    }
    json_text = json.dumps(payload, indent=2)
    md_text = render_compare_markdown(report)

    json_path.write_text(json_text, encoding="utf-8")
    md_path.write_text(md_text, encoding="utf-8")
    latest_json.write_text(json_text, encoding="utf-8")
    latest_md.write_text(md_text, encoding="utf-8")
    return json_path, md_path


def render_markdown(report: EvalReport) -> str:
    lines = [
        f"# Teamwork Coach Evaluation Report (`{report.system}`)",
        "",
        f"- System: **{report.system}**",
        f"- Cases: **{report.case_count}**",
        f"- Suites: {report.suite_counts}",
        "",
        "## Aggregate metrics",
        "",
        "| Metric | n | mean | pass_rate |",
        "| --- | ---: | ---: | ---: |",
    ]
    for agg in report.aggregates:
        mean = f"{agg.mean:.3f}" if agg.mean is not None else "—"
        rate = f"{agg.pass_rate:.3f}" if agg.pass_rate is not None else "—"
        lines.append(f"| `{agg.name}` | {agg.n} | {mean} | {rate} |")

    lines.extend(["", "## Failure codes", ""])
    if report.failure_code_counts:
        for code, count in report.failure_code_counts.items():
            lines.append(f"- `{code}`: {count}")
    else:
        lines.append("- (none)")

    lines.extend(["", "## Per-case summary", ""])
    for case in report.cases:
        failed = ", ".join(case.failure_codes) if case.failure_codes else "ok"
        route = case.observed.route or "error"
        latency = f"{case.observed.latency_ms:.0f}ms"
        err = f" error={case.observed.error}" if case.observed.error else ""
        lines.append(
            f"- `{case.case_id}` [{case.suite}] route={route} "
            f"failures=[{failed}] latency={latency}{err}"
        )

    lines.append("")
    return "\n".join(lines)


def render_compare_markdown(report: CompareReport) -> str:
    lines = [
        "# Advice Quality: Gated Coach vs LLM-only",
        "",
        f"- Cases: **{report.case_count}**",
        f"- Suites: {report.suite_counts}",
        "",
        "This comparison is limited to **advice-quality** metrics "
        "(`actionability`, `forbidden_phrase_free`, and optional `rubric_*`).",
        "Retrieval, citation, and gate metrics are scored on the gated product path only.",
        "",
        "Positive `Δ pass` means the gated coach scored higher on that advice metric.",
        "",
        "| Metric | gated pass | LLM-only pass | Δ pass | gated mean | LLM-only mean |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report.rows:
        g_rate = f"{row.gated_rag_pass_rate:.3f}" if row.gated_rag_pass_rate is not None else "—"
        b_rate = f"{row.no_rag_pass_rate:.3f}" if row.no_rag_pass_rate is not None else "—"
        delta = f"{row.delta_pass_rate:+.3f}" if row.delta_pass_rate is not None else "—"
        g_mean = f"{row.gated_rag_mean:.3f}" if row.gated_rag_mean is not None else "—"
        b_mean = f"{row.no_rag_mean:.3f}" if row.no_rag_mean is not None else "—"
        lines.append(
            f"| `{row.metric}` | {g_rate} | {b_rate} | {delta} | {g_mean} | {b_mean} |"
        )

    lines.extend(
        [
            "",
            "## Advice-quality failure codes",
            "",
            "### gated_rag",
        ]
    )
    if report.gated_rag.failure_code_counts:
        for code, count in report.gated_rag.failure_code_counts.items():
            lines.append(f"- `{code}`: {count}")
    else:
        lines.append("- (none)")

    lines.extend(["", "### LLM-only (no_rag)"])
    advice_failures = {
        k: v
        for k, v in report.no_rag.failure_code_counts.items()
        if k in _ADVICE_FAILURE_CODES
    }
    if advice_failures:
        for code, count in advice_failures.items():
            lines.append(f"- `{code}`: {count}")
    else:
        lines.append("- (none)")

    lines.append("")
    return "\n".join(lines)
