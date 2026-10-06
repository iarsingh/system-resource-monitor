# System Resource Monitor

<!-- project-guide:start -->
## Project guide

[Project architecture](PROJECT_ARCHITECTURE.md) · [Interview questions and answers](INTERVIEW_QA.md)

Use the architecture document for the component diagram, implementation boundaries, and verification entry points. The interview guide includes source-backed answers and project walkthroughs.

### Implementation map

| Component | Responsibility |
| --- | --- |
| [`src/monitor/main.py`](src/monitor/main.py) | HTTP handlers: `GET /healthz`, `POST /check`, `POST /check/series` |
| [`src/monitor/check.py`](src/monitor/check.py) | Functions: `validate`, `check`, `sustained` |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`src/monitor/__init__.py`](src/monitor/__init__.py) | Implementation or supporting configuration |
| [`tests/test_monitor.py`](tests/test_monitor.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |

### Local setup and verification

From the repository root (the commands follow the checked-in manifests):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

To serve the FastAPI application locally, install the server separately if it is not already available:

```bash
python -m pip install uvicorn
PYTHONPATH=src python -m uvicorn monitor.main:app --reload
```

<!-- project-guide:end -->

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

## Ops plane

Workspaces, tenant isolation, job approval, and audit live under `/v1`. Production apply is refused. See `docs/ARCHITECTURE.md`.

## Documentation checks

Project architecture, interview guides, and local source links are checked automatically on pushes and pull requests. Run the same check locally:

```bash
python3 .github/scripts/validate_project_docs.py
```

See [service improvements and local run instructions](docs/UPGRADES.md).
