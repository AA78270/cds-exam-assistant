import json
from datetime import datetime

rows = [json.loads(line) for line in open("logs/agent_traces.jsonl", encoding="utf-8")]

traces = {}
for r in rows:
    traces.setdefault(r["context"]["trace_id"], []).append(r)

for trace_id, spans in traces.items():
    spans.sort(key=lambda s: s["start_time"])
    print(f"\nTRACE {trace_id[-8:]}")
    for s in spans:
        start = datetime.fromisoformat(s["start_time"])
        end = datetime.fromisoformat(s["end_time"])
        ms = round((end - start).total_seconds() * 1000)
        attrs = s.get("attributes", {})
        kind = attrs.get("openinference.span.kind", "-")
        status = s["status"]["status_code"]
        line = f"  {s['name'][:28]:<28} {kind:<6} {ms:>6} ms  {status}"
        if kind == "TOOL":
            line += f"  input={str(attrs.get('input.value', ''))[:80]}"
        print(line)