# OneLap To Strava Sync Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local one-command Python tool that exports FIT files from OneLap and incrementally uploads them to Strava with OAuth refresh, dedupe, and safe retry behavior.

**Architecture:** Use a small layered Python app: CLI -> sync engine -> domain services (`onelap_client`, `dedupe_service`, `strava_client`, `state_store`). Keep orchestration in `sync_engine` and keep all I/O in adapters so future cron/server mode can reuse core logic unchanged.

**Tech Stack:** Python 3.11+, `requests`, `python-dotenv`, `pytest`, `responses`, standard logging/json/hashlib modules.

---

## Preconditions

- Work in a dedicated worktree before coding.
- If behavior is unclear during execution, use `@superpowers/systematic-debugging` before changing code.
- Keep each task small, TDD-first, and commit after green tests.

### Task 1: Project Skeleton and Tooling

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `src/sync_onelap_strava/__init__.py`
- Create: `tests/__init__.py`

**Step 1: Write the failing test**

```python
# tests/test_import_smoke.py
def test_package_importable():
    import sync_onelap_strava

    assert sync_onelap_strava is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_import_smoke.py -v`
Expected: FAIL with `ModuleNotFoundError`.

**Step 3: Write minimal implementation**

```python
# src/sync_onelap_strava/__init__.py
__all__ = ["__version__"]
__version__ = "0.1.0"
```

Also set `pyproject.toml` package path and pytest config.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_import_smoke.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add pyproject.toml requirements.txt requirements-dev.txt src/sync_onelap_strava/__init__.py tests/__init__.py tests/test_import_smoke.py
git commit -m "chore: bootstrap project skeleton and test tooling"
```

### Task 2: Config Loader (.env + CLI override)

**Files:**
- Create: `src/sync_onelap_strava/config.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing test**

```python
from sync_onelap_strava.config import load_settings


def test_default_lookback_days_is_3(monkeypatch):
    monkeypatch.delenv("DEFAULT_LOOKBACK_DAYS", raising=False)
    s = load_settings(cli_since=None)
    assert s.default_lookback_days == 3
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py::test_default_lookback_days_is_3 -v`
Expected: FAIL with `ImportError` or missing symbol.

**Step 3: Write minimal implementation**

```python
# config.py
from dataclasses import dataclass
from datetime import date


@dataclass
class Settings:
    default_lookback_days: int
    cli_since: date | None


def load_settings(cli_since):
    return Settings(default_lookback_days=3, cli_since=cli_since)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/sync_onelap_strava/config.py tests/test_config.py
git commit -m "feat: add settings loader with 3-day default window"
```

### Task 3: State Store (JSON persistence)

**Files:**
- Create: `src/sync_onelap_strava/state_store.py`
- Create: `tests/test_state_store.py`

**Step 1: Write the failing test**

```python
from sync_onelap_strava.state_store import JsonStateStore


def test_add_and_check_synced_record(tmp_path):
    store = JsonStateStore(tmp_path / "state.json")
    fp = "abc123|2026-03-10T08:00:00Z"
    assert not store.is_synced(fp)
    store.mark_synced(fp, strava_activity_id=42)
    assert store.is_synced(fp)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_state_store.py::test_add_and_check_synced_record -v`
Expected: FAIL (missing module/class).

**Step 3: Write minimal implementation**

```python
# store JSON schema: {"synced": {fingerprint: {"strava_activity_id": int, "synced_at": str}}}
```

Implement `is_synced`, `mark_synced`, `last_success_sync_time`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_state_store.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/sync_onelap_strava/state_store.py tests/test_state_store.py
git commit -m "feat: add json state store for synced fingerprints"
```

### Task 4: Dedupe Service (hash + start_time fingerprint)

**Files:**
- Create: `src/sync_onelap_strava/dedupe_service.py`
- Create: `tests/test_dedupe_service.py`

**Step 1: Write the failing test**

```python
from sync_onelap_strava.dedupe_service import make_fingerprint


def test_fingerprint_uses_hash_and_start_time(tmp_path):
    fit_file = tmp_path / "a.fit"
    fit_file.write_bytes(b"fit-content")
    fp = make_fingerprint(fit_file, "2026-03-10T08:00:00Z")
    assert "|2026-03-10T08:00:00Z" in fp
    assert len(fp.split("|")[0]) == 64
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_dedupe_service.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**

```python
# make_fingerprint(path, start_time) -> "<sha256>|<start_time>"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_dedupe_service.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/sync_onelap_strava/dedupe_service.py tests/test_dedupe_service.py
git commit -m "feat: implement fingerprint-based dedupe service"
```

### Task 5: Strava OAuth Token Manager

**Files:**
- Create: `src/sync_onelap_strava/strava_client.py`
- Create: `tests/test_strava_oauth.py`

**Step 1: Write the failing test**

```python
import responses
from sync_onelap_strava.strava_client import StravaClient


@responses.activate
def test_refresh_token_called_when_access_token_expired(tmp_path):
    responses.add(
        responses.POST,
        "https://www.strava.com/oauth/token",
        json={"access_token": "new-token", "refresh_token": "new-refresh", "expires_at": 9999999999},
        status=200,
    )
    client = StravaClient(client_id="id", client_secret="secret", refresh_token="old", access_token="expired", expires_at=0)
    token = client.ensure_access_token()
    assert token == "new-token"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_strava_oauth.py::test_refresh_token_called_when_access_token_expired -v`
Expected: FAIL.

**Step 3: Write minimal implementation**

```python
# ensure_access_token(): if expired -> POST /oauth/token with grant_type=refresh_token
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_strava_oauth.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/sync_onelap_strava/strava_client.py tests/test_strava_oauth.py
git commit -m "feat: implement strava oauth refresh flow"
```

### Task 6: Strava Upload + Poll Result

**Files:**
- Modify: `src/sync_onelap_strava/strava_client.py`
- Create: `tests/test_strava_upload.py`

**Step 1: Write the failing test**

```python
def test_upload_fit_and_poll_until_ready(...):
    # mock POST /api/v3/uploads then GET /api/v3/uploads/{id}
    # assert returns successful activity id
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_strava_upload.py -v`
Expected: FAIL (missing upload implementation).

**Step 3: Write minimal implementation**

```python
# upload_fit(path) -> upload_id
# poll_upload(upload_id) -> {status, error, activity_id}
```

Add bounded polling and 5xx retry policy.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_strava_upload.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/sync_onelap_strava/strava_client.py tests/test_strava_upload.py
git commit -m "feat: add strava fit upload and upload status polling"
```

### Task 7: OneLap Client Adapter

**Files:**
- Create: `src/sync_onelap_strava/onelap_client.py`
- Create: `tests/test_onelap_client.py`
- Create: `docs/reference/onelap-adapter-notes.md`

**Step 1: Write the failing test**

```python
from datetime import date
from sync_onelap_strava.onelap_client import OneLapClient


def test_list_fit_activities_after_since_date(fake_onelap_backend):
    c = OneLapClient(fake_onelap_backend)
    items = c.list_fit_activities(since=date(2026, 3, 7), limit=50)
    assert all(i.start_time >= "2026-03-07" for i in items)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_onelap_client.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**

```python
# Define protocol-like adapter:
# - login()
# - list_fit_activities(since, limit)
# - download_fit(activity_id, output_dir)
```

Document exactly which methods from `SyncOnelapToXoss` are wrapped in `docs/reference/onelap-adapter-notes.md`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_onelap_client.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/sync_onelap_strava/onelap_client.py tests/test_onelap_client.py docs/reference/onelap-adapter-notes.md
git commit -m "feat: add onelap adapter interface and since-date filtering"
```

### Task 8: Sync Engine Orchestration

**Files:**
- Create: `src/sync_onelap_strava/sync_engine.py`
- Create: `tests/test_sync_engine.py`

**Step 1: Write the failing test**

```python
def test_sync_engine_uploads_only_unsynced_items(fake_services):
    # given 3 items and 2 already synced
    # when run_once()
    # then only 1 upload is called and summary matches
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_sync_engine.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**

```python
# run_once() steps:
# 1) compute since_date
# 2) fetch + download
# 3) fingerprint + dedupe
# 4) upload + poll
# 5) mark success in state
# 6) return summary dataclass
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_sync_engine.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/sync_onelap_strava/sync_engine.py tests/test_sync_engine.py
git commit -m "feat: orchestrate incremental sync flow in sync engine"
```

### Task 9: CLI Entry (`python run_sync.py`)

**Files:**
- Create: `run_sync.py`
- Create: `tests/test_cli.py`

**Step 1: Write the failing test**

```python
def test_cli_accepts_since_argument_and_prints_summary(...):
    # run python run_sync.py --since 2026-03-01
    # assert exit code 0 and summary line exists
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**

```python
# argparse with --since
# call sync_engine.run_once()
# print: "fetched X -> deduped Y -> success A -> failed B"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add run_sync.py tests/test_cli.py
git commit -m "feat: add one-command local sync cli"
```

### Task 10: Error Handling and Retry Policy

**Files:**
- Modify: `src/sync_onelap_strava/sync_engine.py`
- Modify: `src/sync_onelap_strava/strava_client.py`
- Create: `tests/test_retry_and_failures.py`

**Step 1: Write the failing test**

```python
def test_onelap_risk_control_stops_current_run(fake_services):
    # onelap returns risk-control exception
    # sync exits safely and reports aborted reason
    ...


def test_strava_5xx_uses_backoff_then_succeeds(fake_services):
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_retry_and_failures.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**

```python
# Introduce explicit exceptions:
# - OnelapRiskControlError
# - StravaRetriableError
# - StravaPermanentError
```

Implement safe abort for risk control and exponential backoff for retriable uploads.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_retry_and_failures.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/sync_onelap_strava/sync_engine.py src/sync_onelap_strava/strava_client.py tests/test_retry_and_failures.py
git commit -m "feat: enforce safe abort and retry strategy for external errors"
```

### Task 11: Logging and Local Observability

**Files:**
- Create: `src/sync_onelap_strava/logging_setup.py`
- Modify: `run_sync.py`
- Create: `tests/test_logging_output.py`

**Step 1: Write the failing test**

```python
def test_run_creates_log_file_with_summary(tmp_path, monkeypatch):
    # assert log file exists under logs/
    # assert includes success/failed counters
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_logging_output.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**

```python
# configure rotating file + console logging
# mask secrets in logged config values
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_logging_output.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/sync_onelap_strava/logging_setup.py run_sync.py tests/test_logging_output.py
git commit -m "feat: add local logs and safe summary output"
```

### Task 12: End-to-End Dry Run Test and User Docs

**Files:**
- Create: `tests/test_e2e_dry_run.py`
- Create: `README.md`
- Create: `.env.example`

**Step 1: Write the failing test**

```python
def test_e2e_dry_run_report_format(fake_services):
    # simulate fetch=8 deduped=3 success=3 failed=0
    # assert printed summary matches required format
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_e2e_dry_run.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**

```markdown
# README should include:
# - setup steps
# - OAuth first-run steps
# - one-command run example
# - --since usage
# - troubleshooting section
```

Also add `.env.example` with required keys.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_e2e_dry_run.py -v && pytest -v`
Expected: PASS for all tests.

**Step 5: Commit**

```bash
git add tests/test_e2e_dry_run.py README.md .env.example
git commit -m "docs: add usage guide and finalize e2e acceptance checks"
```

## Final Verification Checklist

- Run: `pytest -v`
- Run: `python run_sync.py --help`
- Run: `python run_sync.py --since 2026-03-01` (with test credentials)
- Confirm summary format and non-zero exit code on fatal failures.

## Notes for Phase 2 (Server Cron Mode)

- Keep `sync_engine` pure and reusable.
- Add a new entrypoint (cron/job) without changing domain services.
- Reuse same state schema and retry semantics.
