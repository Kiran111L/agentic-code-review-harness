import csv
import json
from pathlib import Path

from .harness import run_review, run_baseline_review
from .scoring import score_findings


async def run_benchmark_impl(mode, approve_paid_calls, output_dir):
    base = Path("samples")
    out = Path("benchmarks")
    out.mkdir(parents=True, exist_ok=True)

    truth_path = base / "ground_truth.json"
    ground_truth = json.loads(truth_path.read_text(encoding="utf-8"))

    rows = []

    for task_id in ("task_1", "task_2", "task_3"):
        project = base / task_id
        expected = ground_truth.get(task_id, [])

        task = (
            f"Review {task_id} for correctness, security, "
            "reliability and maintainability."
        )

        approaches = (
            ("multi_agent", run_review),
            ("single_agent_baseline", run_baseline_review),
        )

        for approach, runner in approaches:
            report, paths = await runner(
                task=task,
                path=str(project),
                mode=mode,
                approve_paid_calls=approve_paid_calls,
                output_dir=output_dir,
            )

            accepted = [
                finding.model_dump()
                if hasattr(finding, "model_dump")
                else finding
                for finding in report.accepted_findings
            ]

            scores = score_findings(expected, accepted)

            rows.append({
                "task_id": task_id,
                "approach": approach,
                "mode": mode,
                "run_status": report.status.value,
                "accepted_findings": len(report.accepted_findings),
                "rejected_findings": len(report.rejected_findings),
                **scores,
                "elapsed_seconds": report.metrics.get("elapsed_seconds"),
                "input_tokens_estimated": report.metrics.get(
                    "input_tokens_estimated"
                ),
                "output_tokens": report.metrics.get("output_tokens"),
                "cost_usd": report.metrics.get("cost_usd"),
                "note": (
                    "Multi-agent specialist workflow"
                    if approach == "multi_agent"
                    else "Independent single-agent baseline workflow"
                ),
                "report_json": paths["json"],
            })

    if not rows:
        raise RuntimeError("Benchmark produced no results.")

    csv_path = out / "comparison.csv"

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    md_path = out / "comparison.md"

    lines = [
        "# Benchmark comparison",
        "",
        (
            "Results are scored against samples/ground_truth.json. Only "
            "accepted findings count as detections. Matching uses category "
            "and file basename, so these are approximate benchmark metrics, "
            "not proof of semantic correctness. Unlisted legitimate issues "
            "may be counted as false positives."
        ),
        "",
        "| Task | Approach | Status | Accepted | TP | FP | FN | Precision | Recall | F1 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in rows:
        lines.append(
            f"| {row['task_id']} "
            f"| {row['approach']} "
            f"| {row['run_status']} "
            f"| {row['accepted_findings']} "
            f"| {row['true_positives']} "
            f"| {row['false_positives']} "
            f"| {row['false_negatives']} "
            f"| {row['precision']:.4f} "
            f"| {row['recall']:.4f} "
            f"| {row['f1']:.4f} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- TP: accepted finding matched an expected issue.",
        "- FP: accepted finding did not match an unmatched expected issue.",
        "- FN: expected issue not detected by an accepted finding.",
        "- Precision = TP / (TP + FP); recall = TP / (TP + FN).",
        "- F1 is the harmonic mean of precision and recall.",
        "- Mock-mode results test workflow mechanics, not model quality.",
        "",
    ])

    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Benchmark complete: {len(rows)} runs")
    print(f"CSV: {csv_path}")
    print(f"Markdown: {md_path}")

    return rows, str(csv_path), str(md_path)
