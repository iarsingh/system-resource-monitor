# System Resource Monitor

Level: 1 — Python fundamentals

Skills: Python, thresholds, a small REST check

Send CPU, memory, and disk percents. A reading at or above 90 is an alert. The check does not read a live host and does not page anyone.

```bash
pip install -r requirements.txt
pytest -q
```
