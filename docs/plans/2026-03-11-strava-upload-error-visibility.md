# Strava Upload Error Visibility Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Show concrete Strava upload failure reasons (HTTP response body and upload poll error) in console/log output so a failed sync can be diagnosed from one run.

**Architecture:** Keep the existing sync flow (`upload_fit -> poll_upload -> summary`) and only add observability where failure currently gets swallowed. Surface HTTP 4xx payload details from the Strava client, then log structured per-activity failure context in the sync engine. Do not add new storage/state fields unless required by tests.

**Tech Stack:** Python 3.14, `requests`, `pytest`, `responses`, stdlib `logging`

---

### Task 1: Surface Strava 4xx Body in `StravaPermanentError`

**Files:**
- Modify: `src/sync_onelap_strava/strava_client.py:56-87`
- Test: `tests/test_strava_upload.py`

**Skill refs:** `@test-driven-development`

**Step 1: Write the failing test**

Add this test to `tests/test_strava_upload.py`:

```python
import pytest
import responses

from sync_onelap_strava.strava_client import StravaClient, StravaPermanentError


@responses.activate
def test_upload_fit_includes_strava_error_payload_on_4xx(tmp_path):
    fit_file = tmp_path / "sample.fit"
    fit_file.write_bytes(b"fit-bytes")

    responses.add(
        responses.POST,
        "https://www.strava.com/api/v3/uploads",
        json={
            "message": "Bad Request",
            "errors": [{"resource": "Upload", "field": "file", "code": "invalid"}],
        },
        status=400,
    )

    client = StravaClient(
        client_id="id",
        client_secret="secret",
        refresh_token="refresh",
        access_token="token",
        expires_at=9999999999,
    )

    with pytest.raises(StravaPermanentError) as exc:
        client.upload_fit(fit_file)

    message = str(exc.value)
    assert "400" in message
    assert "Bad Request" in message
    assert "invalid" in message
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_strava_upload.py::test_upload_fit_includes_strava_error_payload_on_4xx -v`

Expected: FAIL because current exception text only contains status code, not response payload.

**Step 3: Write minimal implementation**

In `src/sync_onelap_strava/strava_client.py` update the `response.status_code >= 400` branch in `upload_fit` to include response details:

```python
if response.status_code >= 400:
    detail = ""
    try:
        detail = str(response.json())
    except ValueError:
        detail = response.text.strip()
    if detail:
        raise StravaPermanentError(
            f"strava upload failed: {response.status_code} detail={detail}"
        )
    raise StravaPermanentError(f"strava upload failed: {response.status_code}")
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_strava_upload.py::test_upload_fit_includes_strava_error_payload_on_4xx -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_strava_upload.py src/sync_onelap_strava/strava_client.py
git commit -m "fix: include Strava 4xx payload in upload errors"
```

### Task 2: Log Poll Failure Details per Activity in Sync Engine

**Files:**
- Modify: `src/sync_onelap_strava/sync_engine.py:1-82`
- Test: `tests/test_sync_engine.py`

**Skill refs:** `@test-driven-development`

**Step 1: Write the failing test**

Add this test to `tests/test_sync_engine.py`:

```python
import logging
from pathlib import Path

from sync_onelap_strava.sync_engine import SyncEngine


def test_sync_engine_logs_poll_error_details(tmp_path, caplog):
    class FakeItem:
        def __init__(self, activity_id, start_time):
            self.activity_id = activity_id
            self.start_time = start_time

    class FakeOnelap:
        def list_fit_activities(self, since, limit):
            return [FakeItem("a1", "2026-03-10T08:00:00Z")]

        def download_fit(self, activity_id, output_dir):
            path = Path(output_dir) / f"{activity_id}.fit"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fit")
            return path

    class FakeState:
        def is_synced(self, fingerprint):
            return False

        def mark_synced(self, fingerprint, strava_activity_id):
            raise AssertionError("should not mark synced on error")

    class FakeStrava:
        def upload_fit(self, path):
            return 123

        def poll_upload(self, upload_id):
            return {
                "status": "error",
                "error": "duplicate of activity 999",
                "activity_id": None,
            }

    def fake_make_fingerprint(path, start_time):
        return f"fp|{start_time}"

    caplog.set_level(logging.ERROR, logger="sync_onelap_strava")

    engine = SyncEngine(
        onelap_client=FakeOnelap(),
        strava_client=FakeStrava(),
        state_store=FakeState(),
        make_fingerprint=fake_make_fingerprint,
        download_dir=tmp_path,
    )

    summary = engine.run_once(since_date="2026-03-07", limit=50)

    assert summary.success == 0
    assert summary.failed == 1
    assert "duplicate of activity 999" in caplog.text
    assert "a1" in caplog.text
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sync_engine.py::test_sync_engine_logs_poll_error_details -v`

Expected: FAIL because `SyncEngine` does not currently log poll error details.

**Step 3: Write minimal implementation**

In `src/sync_onelap_strava/sync_engine.py`:

```python
import logging

LOGGER = logging.getLogger("sync_onelap_strava")
```

Then inside `run_once`, in the branch where `activity_id is None or result.get("error") is not None`, add:

```python
LOGGER.error(
    "strava upload failed activity_id=%s upload_id=%s status=%s error=%s",
    item.activity_id,
    upload_id,
    result.get("status"),
    result.get("error"),
)
```

Leave current control flow unchanged (`failed += 1`, `continue`).

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sync_engine.py::test_sync_engine_logs_poll_error_details -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_sync_engine.py src/sync_onelap_strava/sync_engine.py
git commit -m "fix: log Strava poll error details per activity"
```

### Task 3: Log Exception Details from Upload/Poll Exceptions

**Files:**
- Modify: `src/sync_onelap_strava/sync_engine.py:68-79`
- Test: `tests/test_sync_engine.py`

**Skill refs:** `@test-driven-development`

**Step 1: Write the failing test**

Add this test to `tests/test_sync_engine.py`:

```python
import logging
from pathlib import Path

from sync_onelap_strava.sync_engine import SyncEngine


def test_sync_engine_logs_exception_message_when_upload_raises(tmp_path, caplog):
    class FakeItem:
        def __init__(self, activity_id, start_time):
            self.activity_id = activity_id
            self.start_time = start_time

    class FakeOnelap:
        def list_fit_activities(self, since, limit):
            return [FakeItem("a1", "2026-03-10T08:00:00Z")]

        def download_fit(self, activity_id, output_dir):
            path = Path(output_dir) / f"{activity_id}.fit"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fit")
            return path

    class FakeState:
        def is_synced(self, fingerprint):
            return False

        def mark_synced(self, fingerprint, strava_activity_id):
            raise AssertionError("should not mark synced on exception")

    class FakeStrava:
        def upload_fit(self, path):
            raise RuntimeError("403 forbidden: missing scope activity:write")

        def poll_upload(self, upload_id):
            raise AssertionError("poll should not be called")

    def fake_make_fingerprint(path, start_time):
        return f"fp|{start_time}"

    caplog.set_level(logging.ERROR, logger="sync_onelap_strava")

    engine = SyncEngine(
        onelap_client=FakeOnelap(),
        strava_client=FakeStrava(),
        state_store=FakeState(),
        make_fingerprint=fake_make_fingerprint,
        download_dir=tmp_path,
    )

    summary = engine.run_once(since_date="2026-03-07", limit=50)

    assert summary.success == 0
    assert summary.failed == 1
    assert "activity:write" in caplog.text
    assert "a1" in caplog.text
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sync_engine.py::test_sync_engine_logs_exception_message_when_upload_raises -v`

Expected: FAIL because exception details are currently swallowed.

**Step 3: Write minimal implementation**

Replace the broad exception block in `src/sync_onelap_strava/sync_engine.py` with:

```python
except Exception as exc:
    LOGGER.error(
        "strava upload exception activity_id=%s error=%s",
        item.activity_id,
        exc,
    )
    failed += 1
```

Keep behavior unchanged (still counts as failed and continues).

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sync_engine.py::test_sync_engine_logs_exception_message_when_upload_raises -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_sync_engine.py src/sync_onelap_strava/sync_engine.py
git commit -m "fix: log upload exception details during sync"
```

### Task 4: Regression Run + Docs Update

**Files:**
- Modify: `README.md:55-61`

**Skill refs:** `@verification-before-completion`

**Step 1: Write the failing docs check (human-readable expectation)**

Expectation to add in Troubleshooting: logs now include Strava status/error details for failed uploads.

**Step 2: Run focused test suite before docs change**

Run: `python -m pytest tests/test_strava_upload.py tests/test_sync_engine.py -v`

Expected: PASS (code behavior complete before documentation).

**Step 3: Write minimal documentation update**

Add one bullet under Troubleshooting in `README.md`:

```markdown
- If sync reports failed uploads, check `logs/sync.log`; each failure line now includes Strava `status` and `error` details.
```

**Step 4: Run final verification**

Run:

```bash
python -m pytest tests/test_strava_upload.py tests/test_sync_engine.py tests/test_cli.py tests/test_logging_output.py -v
python run_sync.py --since 2026-03-10
```

Expected:
- All listed tests PASS.
- Runtime output still prints summary line.
- On failure, console/log now shows detailed error context.

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add guidance for Strava upload error diagnostics"
```
