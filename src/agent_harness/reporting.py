import json
from pathlib import Path
from .schemas import FinalReport

def write_report(report: FinalReport, output_dir: str):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / f"{report.run_id}.json"
    md_path = out / f"{report.run_id}.md"
    json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    lines = [f"# Code Review Report — {report.run_id}", "", f"**Status:** {report.status.value}", "", report.summary, "", "## Accepted findings", ""]
    if not report.accepted_findings:
        lines.append("No findings accepted. In mock mode, this is a simulation, not evidence of code quality.")
    for f in report.accepted_findings:
        lines += [f"### [{f.severity.value.upper()}] {f.title}", "", f"- **Location:** `{f.file_path}:{f.start_line}-{f.end_line}`", f"- **Category:** {f.category.value}", f"- **Evidence:** `{f.evidence}`", f"- **Issue:** {f.explanation}", f"- **Conditions:** {f.conditions or 'Not specified'}", f"- **Recommended fix:** {f.recommended_fix}", f"- **Confidence:** {f.confidence:.2f}", ""]
    lines += ["## Rejected / unverified findings", ""]
    lines += [f"- {item.get('reason','No reason')} — {item.get('finding',{}).get('title','unknown finding')}" for item in report.rejected_findings] or ["None."]
    lines += ["", "## Agent results", ""]
    for r in report.agent_results:
        lines.append(f"- **{r.role.value}**: {r.status.value}; findings={len(r.findings)}; elapsed={r.elapsed_seconds:.2f}s; errors={'; '.join(r.errors) or 'none'}")
    lines += ["", "## Metrics", "", "```json", json.dumps(report.metrics, indent=2), "```", "", f"Trace: `{report.trace_file}`", ""]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return str(json_path), str(md_path)
