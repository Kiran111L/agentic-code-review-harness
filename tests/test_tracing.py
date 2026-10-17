import json
from agent_harness.tracing import Trace

def test_trace_jsonl(tmp_path):
    p=tmp_path/"trace.jsonl"
    t=Trace(str(p),"run")
    t.emit("started", message="ok")
    item=json.loads(p.read_text().splitlines()[0])
    assert item["event"]=="started" and item["run_id"]=="run"
