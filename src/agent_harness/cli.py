import argparse, asyncio, json, sys
from pathlib import Path
from .harness import run_review, run_benchmark
from .tracing import replay

def parser():
    p = argparse.ArgumentParser(prog="agent_harness")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="Run a code review")
    r.add_argument("--task", required=True)
    r.add_argument("--path", required=True)
    r.add_argument("--mode", choices=("mock", "ollama", "live"), default="mock")
    r.add_argument("--approve-paid-calls", action="store_true")
    r.add_argument("--output-dir", default="runs")
    b = sub.add_parser("benchmark", help="Run three synthetic benchmark tasks")
    b.add_argument("--mode", choices=("mock", "ollama", "live"), default="mock")
    b.add_argument("--approve-paid-calls", action="store_true")
    b.add_argument("--output-dir", default="runs")
    rp = sub.add_parser("replay", help="Replay a JSONL trace without model calls")
    rp.add_argument("--trace", required=True)
    return p

def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "replay":
            replay(args.trace); return 0
        if args.command == "run":
            report, paths = asyncio.run(run_review(args.task, args.path, args.mode, args.approve_paid_calls, args.output_dir))
            print(f"Status: {report.status.value}\nSummary: {report.summary}")
            print(f"JSON report: {paths['json']}\nMarkdown report: {paths['markdown']}\nTrace: {paths['trace']}")
            return 0 if report.status.value == "completed" else 2
        rows, csv_path, md_path = asyncio.run(run_benchmark(args.mode, args.approve_paid_calls, args.output_dir))
        print(f"Benchmark mechanics complete: {len(rows)} runs\nCSV: {csv_path}\nMarkdown: {md_path}")
        return 0
    except Exception as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
