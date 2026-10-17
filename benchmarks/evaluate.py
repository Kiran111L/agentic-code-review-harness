#!/usr/bin/env python3
"""Evaluate benchmark reports against benchmarks/ground_truth.json.

Usage from the repository root:
    python benchmarks/evaluate.py
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCHMARK_DIR = ROOT / "benchmarks"
GROUND_TRUTH_PATH = BENCHMARK_DIR / "ground_truth.json"
COMPARISON_PATH = BENCHMARK_DIR / "comparison.csv"
OUTPUT_CSV = BENCHMARK_DIR / "evaluation.csv"
OUTPUT_MD = BENCHMARK_DIR / "evaluation.md"


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def get_accepted_findings(report):
    findings = report.get("accepted_findings", [])
    return [item for item in findings if isinstance(item, dict)]


def finding_matches(expected, actual, line_tolerance):
    actual_path = Path(str(actual.get("file_path", ""))).name
    expected_path = Path(str(expected.get("file_path", ""))).name
    if actual_path != expected_path:
        return False

    if str(actual.get("category", "")).lower() != str(expected.get("category", "")).lower():
        return False

    try:
        actual_line = int(actual.get("start_line", 0))
    except (TypeError, ValueError):
        return False

    return abs(actual_line - int(expected["line"])) <= line_tolerance


def score_one(task_id, approach, report_path, ground_truth, line_tolerance):
    expected = ground_truth["tasks"].get(task_id, [])
    report = load_json(report_path)
    actual = get_accepted_findings(report)

    matched_expected_ids = set()
    matched_actual_indices = set()

    # Greedy one-to-one matching: one reported finding cannot satisfy multiple labels.
    for actual_index, finding in enumerate(actual):
        for expected_index, label in enumerate(expected):
            if expected_index in matched_expected_ids:
                continue
            if finding_matches(label, finding, line_tolerance):
                matched_expected_ids.add(expected_index)
                matched_actual_indices.add(actual_index)
                break

    tp = len(matched_actual_indices)
    fp = len(actual) - tp
    fn = len(expected) - len(matched_expected_ids)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0

    return {
        "task_id": task_id,
        "approach": approach,
        "run_status": report.get("status", "unknown"),
        "expected_findings": len(expected),
        "accepted_findings": len(actual),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "report_json": str(report_path),
    }


def main():
    if not GROUND_TRUTH_PATH.exists():
        raise SystemExit(f"Ground-truth file not found: {GROUND_TRUTH_PATH}")
    if not COMPARISON_PATH.exists():
        raise SystemExit(
            "Benchmark CSV not found. Run `python -m agent_harness benchmark --mode mock` first."
        )

    ground_truth = load_json(GROUND_TRUTH_PATH)
    line_tolerance = int(ground_truth.get("matching", {}).get("line_tolerance", 2))

    with COMPARISON_PATH.open("r", newline="", encoding="utf-8") as file:
        benchmark_rows = list(csv.DictReader(file))

    results = []
    for row in benchmark_rows:
        task_id = row["task_id"]
        approach = row["approach"]
        report_path = Path(row["report_json"])
        if not report_path.is_absolute():
            report_path = ROOT / report_path
        if not report_path.exists():
            print(f"Skipping missing report for {task_id}/{approach}: {report_path}")
            continue
        results.append(
            score_one(task_id, approach, report_path, ground_truth, line_tolerance)
        )

    if not results:
        raise SystemExit("No benchmark reports could be evaluated.")

    fields = list(results[0].keys())
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    approaches = sorted({row["approach"] for row in results})
    lines = [
        "# Ground-truth evaluation",
        "",
        "Scores are computed by matching accepted findings to the labels in `ground_truth.json`.",
        "Matching uses file basename, category, and a configurable line tolerance.",
        "These labels cover only the currently known sample issues; they do not measure every possible issue.",
        "Mock-mode results test deterministic mechanics, not real LLM quality.",
        "",
        "| Approach | Runs scored | TP | FP | FN | Precision | Recall | F1 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for approach in approaches:
        group = [row for row in results if row["approach"] == approach]
        tp = sum(row["true_positives"] for row in group)
        fp = sum(row["false_positives"] for row in group)
        fn = sum(row["false_negatives"] for row in group)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        lines.append(
            f"| {approach} | {len(group)} | {tp} | {fp} | {fn} | "
            f"{precision:.3f} | {recall:.3f} | {f1:.3f} |"
        )

    lines.extend(["", "## Per-task results", ""])
    lines.append("| Task | Approach | TP | FP | FN | Precision | Recall | F1 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for row in results:
        lines.append(
            f"| {row['task_id']} | {row['approach']} | {row['true_positives']} | "
            f"{row['false_positives']} | {row['false_negatives']} | "
            f"{row['precision']:.3f} | {row['recall']:.3f} | {row['f1_score']:.3f} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- A true positive (TP) is an accepted finding matched to a ground-truth label.",
        "- A false positive (FP) is an accepted finding that did not match a label.",
        "- A false negative (FN) is a ground-truth label with no matching accepted finding.",
        "- A score of zero can mean the approach missed all current labels; it does not prove it is generally ineffective.",
        "- Review and expand the ground-truth labels whenever the sample code changes.",
        "",
    ])
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Evaluation complete: {len(results)} report(s) scored")
    print(f"CSV: {OUTPUT_CSV.relative_to(ROOT)}")
    print(f"Markdown: {OUTPUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
