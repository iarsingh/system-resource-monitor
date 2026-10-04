# System Resource Monitor

Level: 1 — Python fundamentals

Skills: Python, thresholds, a small REST check, alert flapping control

Send CPU, memory, and disk percents. A single reading at or above its threshold (90 by default) is an alert.

A series of readings is judged differently, the way an on-call rotation wants it:

- A resource fires only after `window` readings in a row breach (3 by default). One spike does not fire.
- Once firing, it stays firing until a reading falls 10 points below the threshold. A value hovering at 85 under a threshold of 90 does not flap between firing and clear.

```bash
pip install -r requirements.txt
pytest -q
PYTHONPATH=src uvicorn monitor.main:app --reload
```

| Method and path | Body |
| --- | --- |
| `POST /check` | `cpu_percent`, `memory_percent`, `disk_percent`, optional `thresholds` |
| `POST /check/series` | `samples` (1 to 1440), optional `window` (1 to 60) and `thresholds` |

A reading outside 0 to 100, a missing resource, or a value that is not a number is refused. The check does not read a live host and does not page anyone: `paged` is always false.
