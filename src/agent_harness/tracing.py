import json, time, uuid
from datetime import datetime, timezone
from pathlib import Path
from .safety import redact

class Trace:
    def __init__(self, path: str, run_id: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id

    def emit(self, event: str, **fields):
        record = {"timestamp": datetime.now(timezone.utc).isoformat(), "event_id": str(uuid.uuid4()), "run_id": self.run_id, "event": event}
        record.update(fields)
        safe = json.loads(redact(json.dumps(record, default=str)))
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(safe, ensure_ascii=False) + "\n")

def replay(path: str):
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)
    events = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    for item in events:
        print(f"{item.get('timestamp','?')} | {item.get('event','event')} | role={item.get('role','-')} | status={item.get('status','-')} | {item.get('message', '')}")
    print(f"\n{len(events)} events loaded; replay performs no model calls.")
