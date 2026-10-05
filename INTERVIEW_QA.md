# system-resource-monitor — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does system-resource-monitor address, and what can you demonstrate?

Send CPU, memory, and disk percents. A single reading at or above its threshold (90 by default) is an alert.

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/monitor/main.py`](src/monitor/main.py): Implementation or supporting configuration.
- [`src/monitor/check.py`](src/monitor/check.py): Implementation or supporting configuration.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`src/monitor/__init__.py`](src/monitor/__init__.py): Implementation or supporting configuration.
- [`tests/test_monitor.py`](tests/test_monitor.py): Executable checks and regression examples.
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml): GitHub Actions job definitions.
- [`README.md`](README.md): Project explanations or operating notes.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `sustained` and explain the decision it makes?

The main walkthrough here is `sustained(samples, thresholds=None, window=3)` in [`src/monitor/check.py`](src/monitor/check.py#L26).

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
```

This is an excerpt; follow the source link for the rest of the branches.

The implementation calls `ReadingError`, `enumerate`, `validate`. In an interview, trace those calls in execution order using a fixture input.

## 4. What responsibility does `validate` have?

`validate(snapshot)` is defined in [`src/monitor/check.py`](src/monitor/check.py#L10).

It uses `ReadingError`, `isinstance`. This is the code path I would compare against the caller to explain responsibility boundaries.

## 5. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `ReadingError('window must be at least 1')` in [`src/monitor/check.py`](src/monitor/check.py#L28).
- `ReadingError(f'{key} is missing')` in [`src/monitor/check.py`](src/monitor/check.py#L13).
- `ReadingError(f'{key} must be a number from 0 to 100')` in [`src/monitor/check.py`](src/monitor/check.py#L16).
- `HTTPException(status_code=422, detail=str(exc))` in [`src/monitor/main.py`](src/monitor/main.py#L19).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 6. Which test would you use to demonstrate correctness?

[`tests/test_monitor.py`](tests/test_monitor.py#L16) contains `test_cpu_alert`:

```python
def test_cpu_alert():
    payload = client.post("/check", json=sample(cpu=95)).json()
    assert payload["alerts"] == ["cpu_percent"]
    assert payload["paged"] is False
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 7. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/monitor/main.py`](src/monitor/main.py#L23).
- `POST /check` → `post_check` in [`src/monitor/main.py`](src/monitor/main.py#L28).
- `POST /check/series` → `post_series` in [`src/monitor/main.py`](src/monitor/main.py#L34).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 8. Where does state live, and what happens with multiple workers?

Module-level containers include `DEFAULT_THRESHOLDS` in [`src/monitor/check.py`](src/monitor/check.py).

These containers belong to a Python process. Inspect which are constant fixtures and which are mutated. Mutable process state needs an explicit shared-storage or synchronization strategy before multiple workers can provide consistent behavior.

## 9. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 10. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 11. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 12. What is the input-to-output contract of `sustained`?

In [`src/monitor/check.py`](src/monitor/check.py#L26), `sustained(samples, thresholds=None, window=3)` receives the inputs. The function computes these intermediate values:

- `limits = {**DEFAULT_THRESHOLDS, **(thresholds or {})}`
- `state = {key: {'firing': False, 'streak': 0, 'fired_at': None, 'recovered_at': None} for key in RESOURCES}`
- `firing = [key for key in RESOURCES if state[key]['firing']]`

Its result is defined by:

- `{'firing': firing, 'healthy': not firing, 'window': window, 'resources': state, 'paged': False}`

## 13. Which decision rules or boundary conditions should an interviewer challenge?

The implementation in [`src/monitor/check.py`](src/monitor/check.py#L26) branches on:

- `window < 1`
- `value >= limits[key]`
- `not current['firing'] and current['streak'] >= window`
- `current['firing'] and value < limits[key] - RECOVER_GAP`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.
