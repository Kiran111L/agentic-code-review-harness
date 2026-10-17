# Demo script (3–4 minutes)

1. **0:00–0:30 — Explain architecture.** Show README Mermaid diagram and describe planner, three parallel specialists, checker, reports, trace.
2. **0:30–1:10 — Run mock mode.**
   ```bash
   PYTHONPATH=src python -m agent_harness run --task "Review for correctness and security" --path samples/task_1 --mode mock
   ```
   Explain that the default mock provider simulates orchestration and does not measure review quality.
3. **1:10–1:40 — Inspect report and trace.** Open generated Markdown/JSON, then replay the trace:
   ```bash
   PYTHONPATH=src python -m agent_harness replay --trace runs/RUN_ID/trace.jsonl
   ```
4. **1:40–2:15 — Show path permissions.** Run `PYTHONPATH=src pytest -q tests/test_tools.py` to demonstrate traversal and credential-file blocking.
5. **2:15–2:50 — Show a failure.** Run the test `tests/test_failures.py`, which injects a specialist failure through the model stub and asserts that the failure is surfaced. Do not claim successful recovery unless that test passes.
6. **2:50–3:30 — Benchmark.** Run `PYTHONPATH=src python -m agent_harness benchmark --mode mock`. Explain quality scores are pending and the baseline is not yet a genuine separate implementation.
7. **3:30–4:00 — Honest limitations.** Explain that live quality benchmarking, complete correction routing, provider usage reconciliation, and full per-agent budgets remain incomplete.
