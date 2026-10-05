# system-resource-monitor — project architecture

[README](README.md) · [Interview questions and answers](INTERVIEW_QA.md)

## Purpose and scope

Send CPU, memory, and disk percents. A single reading at or above its threshold (90 by default) is an alert.

This document describes files and symbols in this checkout. Deployment templates and statements in the original overview are distinguished from a verified running environment.

## Component diagram

```mermaid
flowchart LR
    M0["src/monitor/__init__.py"]
    M1["src/monitor/check.py"]
    M2["src/monitor/main.py"]
    M2 -->|imports| M1
```

For Python repositories, arrows show resolved local imports, not network calls or deployment order. Otherwise the diagram is a repository component map; containment arrows do not assert runtime integration.

## Components and responsibilities

| Component | Responsibility |
| --- | --- |
| [`src/monitor/main.py`](src/monitor/main.py) | HTTP handlers: `GET /healthz`, `POST /check`, `POST /check/series` |
| [`src/monitor/check.py`](src/monitor/check.py) | Functions: `validate`, `check`, `sustained` |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`src/monitor/__init__.py`](src/monitor/__init__.py) | Implementation or supporting configuration |
| [`tests/test_monitor.py`](tests/test_monitor.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |

## Request interface

| Method and path | Handler | Source |
| --- | --- | --- |
| `GET /healthz` | `healthz` | [`src/monitor/main.py`](src/monitor/main.py#L23) |
| `POST /check` | `post_check` | [`src/monitor/main.py`](src/monitor/main.py#L28) |
| `POST /check/series` | `post_series` | [`src/monitor/main.py`](src/monitor/main.py#L34) |

The table lists literal route decorators found in the inspected Python modules. Router prefixes and middleware can add behavior; check the linked handler and application setup before calling an endpoint.

## Implementation walkthrough

### `sustained(samples, thresholds=None, window=3)`

Source: [`src/monitor/check.py`](src/monitor/check.py#L26).

Calls visible in this function: `ReadingError`, `enumerate`, `validate`.

```python
def sustained(samples, thresholds=None, window=3):
    if window < 1:
        raise ReadingError("window must be at least 1")
    limits = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    for sample in samples:
        validate(sample)
    state = {key: {"firing": False, "streak": 0, "fired_at": None, "recovered_at": None} for key in RESOURCES}
    for index, sample in enumerate(samples):
        for key in RESOURCES:
            current = state[key]
            value = sample[key]
            if value >= limits[key]:
                current["streak"] += 1
                if not current["firing"] and current["streak"] >= window:
                    current["firing"] = True
                    current["fired_at"] = index
                    current["recovered_at"] = None
            else:
                current["streak"] = 0
                if current["firing"] and value < limits[key] - RECOVER_GAP:
                    current["firing"] = False
                    current["recovered_at"] = index
```

The excerpt is truncated; the linked source contains the full implementation.

### `validate(snapshot)`

Source: [`src/monitor/check.py`](src/monitor/check.py#L10).

Calls visible in this function: `ReadingError`, `isinstance`.

```python
def validate(snapshot):
    for key in RESOURCES:
        if key not in snapshot:
            raise ReadingError(f"{key} is missing")
        value = snapshot[key]
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 100:
            raise ReadingError(f"{key} must be a number from 0 to 100")
```

### `check(snapshot, thresholds=None)`

Source: [`src/monitor/check.py`](src/monitor/check.py#L19).

Calls visible in this function: `validate`.

```python
def check(snapshot, thresholds=None):
    validate(snapshot)
    limits = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    alerts = [key for key in RESOURCES if snapshot[key] >= limits[key]]
    return {"alerts": alerts, "healthy": not alerts, "paged": False}
```

### `guarded(action)`

Source: [`src/monitor/main.py`](src/monitor/main.py#L15).

Calls visible in this function: `HTTPException`, `action`, `str`.

```python
def guarded(action):
    try:
        return action()
    except ReadingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
```

## Validation and failure paths

| Explicit exception | Source |
| --- | --- |
| `ReadingError('window must be at least 1')` | [`src/monitor/check.py`](src/monitor/check.py#L28) |
| `ReadingError(f'{key} is missing')` | [`src/monitor/check.py`](src/monitor/check.py#L13) |
| `ReadingError(f'{key} must be a number from 0 to 100')` | [`src/monitor/check.py`](src/monitor/check.py#L16) |
| `HTTPException(status_code=422, detail=str(exc))` | [`src/monitor/main.py`](src/monitor/main.py#L19) |

These are explicit exceptions in the inspected source, rather than a claim that every failure is handled. Follow the calling handler to see whether the exception becomes an HTTP response or propagates.

## Data and state

- [`src/monitor/check.py`](src/monitor/check.py) defines module-level containers: `DEFAULT_THRESHOLDS`.

Module-level dictionaries/lists live in a Python process. They can be fixtures or mutable state; inspect writes before treating them as persistent storage. A production extension would need to define persistence and concurrency behavior explicitly.

## Data flow and design decisions

### What is the input-to-output contract of `sustained`

In [`src/monitor/check.py`](src/monitor/check.py#L26), `sustained(samples, thresholds=None, window=3)` receives the inputs. The function computes these intermediate values:

- `limits = {**DEFAULT_THRESHOLDS, **(thresholds or {})}`
- `state = {key: {'firing': False, 'streak': 0, 'fired_at': None, 'recovered_at': None} for key in RESOURCES}`
- `firing = [key for key in RESOURCES if state[key]['firing']]`

Its result is defined by:

- `{'firing': firing, 'healthy': not firing, 'window': window, 'resources': state, 'paged': False}`

### Which decision rules or boundary conditions should an interviewer challenge

The implementation in [`src/monitor/check.py`](src/monitor/check.py#L26) branches on:

- `window < 1`
- `value >= limits[key]`
- `not current['firing'] and current['streak'] >= window`
- `current['firing'] and value < limits[key] - RECOVER_GAP`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

## Setup and verification

The following commands are derived from the checked-in dependency/test contracts. Execute them from the repository root; the block prepares a local environment, not a cloud deployment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

Python dependencies: [`requirements.txt`](requirements.txt).

Test entry points: [`tests/test_monitor.py`](tests/test_monitor.py).

Automation definitions: [`.github/workflows/ci.yml`](.github/workflows/ci.yml). Read their triggers and job steps to determine what CI actually runs.

## Operating boundaries and design review

Before turning this checkout into a customer deployment, establish the input contract, data ownership, access controls, failure response, evaluation criteria, and rollback owner. Repository fixtures and unit tests demonstrate local behavior; they do not establish throughput, uptime, compliance, or business impact.

A useful architecture review starts with the linked implementation: identify where input enters, where a decision is made, which state can change, and which external dependency can fail. Add a deployment view only for infrastructure that is actually configured and exercised.
