# OneLap Multi-FIT Dedupe Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Support multiple FIT files under the same OneLap `activity_id`, prevent local overwrite, and classify Strava duplicate responses as deduped instead of failed.

**Architecture:** Promote the pipeline from activity-level identity to file-level identity. Introduce a stable `record_key` derived from `fileKey/fitUrl/durl`, carry it from OneLap list through download and sync dedupe, and update upload result handling so Strava duplicate responses are treated as dedupe and persisted in state.

**Tech Stack:** Python 3.14, `requests`, `pytest`, `responses`, existing `run_sync.py` CLI and `sync_onelap_strava` modules.

---

### Task 1: Extend OneLap item model to file-level identity

**Files:**
- Modify: `src/sync_onelap_strava/onelap_client.py`
- Test: `tests/test_onelap_client.py`

**Step 1: Write the failing test**

Add to `tests/test_onelap_client.py`:

```python
@responses.activate
def test_list_fit_activities_keeps_multiple_records_with_same_activity_id():
    responses.add(
        responses.GET,
        "http://u.onelap.cn/analysis/list",
        json={
            "data": [
                {
                    "id": "677767",
                    "start_time": "2026-03-12T08:00:00Z",
                    "fitUrl": "/fit/MAGENE_A.fit",
                    "fileKey": "MAGENE_A.fit",
                },
                {
                    "id": "677767",
                    "start_time": "2026-03-12T09:00:00Z",
                    "fitUrl": "/fit/MAGENE_B.fit",
                    "fileKey": "MAGENE_B.fit",
                },
            ]
        },
        status=200,
    )

    c = OneLapClient(base_url="https://www.onelap.cn", username="u", password="p")
    items = c.list_fit_activities(since=date(2026, 3, 12), limit=50)

    assert len(items) == 2
    assert items[0].activity_id == "677767"
    assert items[1].activity_id == "677767"
    assert items[0].record_key != items[1].record_key
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_onelap_client.py::test_list_fit_activities_keeps_multiple_records_with_same_activity_id -v`

Expected: FAIL because `record_key` does not exist yet.

**Step 3: Write minimal implementation**

In `src/sync_onelap_strava/onelap_client.py`:
- Extend `OneLapActivity` dataclass with `record_key` and `source_filename`.
- Build a helper that selects identity source in priority order: `fileKey`, then `fitUrl`, then `durl`.
- Create stable `record_key` from selected source and use it for internal mapping.
- Keep `activity_id` unchanged for logging compatibility.

Minimal code shape:

```python
@dataclass
class OneLapActivity:
    activity_id: str
    start_time: str
    fit_url: str
    record_key: str
    source_filename: str
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_onelap_client.py::test_list_fit_activities_keeps_multiple_records_with_same_activity_id -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_onelap_client.py src/sync_onelap_strava/onelap_client.py
git commit -m "feat: add file-level OneLap record identity"
```

### Task 2: Switch download API and naming to record-based files

**Files:**
- Modify: `src/sync_onelap_strava/onelap_client.py`
- Modify: `run_sync.py`
- Test: `tests/test_onelap_download.py`
- Test: `tests/test_cli_download_only.py`

**Step 1: Write failing tests for naming priority and no overwrite**

Add to `tests/test_onelap_download.py`:

```python
@responses.activate
def test_download_fit_uses_source_filename_priority(tmp_path):
    responses.add(
        responses.GET,
        "http://u.onelap.cn/analysis/list",
        json={
            "data": [
                {
                    "id": "a2",
                    "start_time": "2026-03-08T08:00:00Z",
                    "fitUrl": "/fit/from-fiturl.fit",
                    "fileKey": "MAGENE_REAL.fit",
                    "durl": "/fit/fallback.fit",
                }
            ]
        },
        status=200,
    )
    responses.add(
        responses.GET,
        "https://www.onelap.cn/fit/from-fiturl.fit",
        body=b"fit-bytes",
        status=200,
        content_type="application/octet-stream",
    )

    c = OneLapClient(base_url="https://www.onelap.cn", username="u", password="p")
    item = c.list_fit_activities(since=__import__("datetime").date(2026, 3, 1), limit=50)[0]
    path = c.download_fit(item.record_key, tmp_path)

    assert path.name == "MAGENE_REAL.fit"
```

Add to `tests/test_cli_download_only.py` (update fake item shape and assertion):

```python
class Item:
    def __init__(self, activity_id, start_time, record_key, source_filename):
        self.activity_id = activity_id
        self.start_time = start_time
        self.record_key = record_key
        self.source_filename = source_filename
```

Expected output assertions should use `source_filename` instead of hard-coded `activity_id.fit`.

**Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_onelap_download.py::test_download_fit_uses_source_filename_priority -v
python -m pytest tests/test_cli_download_only.py -v
```

Expected: FAIL because current API is activity-id based and filename is `{activity_id}.fit`.

**Step 3: Write minimal implementation**

In `src/sync_onelap_strava/onelap_client.py`:
- Change cache to `record_key -> (fit_url, source_filename)`.
- Change `download_fit` signature to accept `record_key`.
- Sanitize preferred filename, enforce `.fit`, resolve collisions safely.

In `run_sync.py`:
- In download-only mode, call `download_fit(item.record_key, Path("downloads"))`.
- Print `Path(returned_path).name` instead of synthesizing `activity_id.fit`.

**Step 4: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/test_onelap_download.py -v
python -m pytest tests/test_cli_download_only.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_onelap_download.py tests/test_cli_download_only.py src/sync_onelap_strava/onelap_client.py run_sync.py
git commit -m "feat: use source filename and record-key downloads"
```

### Task 3: Upgrade fingerprint to include record key

**Files:**
- Modify: `src/sync_onelap_strava/dedupe_service.py`
- Test: `tests/test_dedupe_service.py`

**Step 1: Write failing test**

Replace/add in `tests/test_dedupe_service.py`:

```python
def test_fingerprint_uses_record_key_hash_and_start_time(tmp_path):
    fit_file = tmp_path / "a.fit"
    fit_file.write_bytes(b"fit-content")

    fp = make_fingerprint(
        path=fit_file,
        start_time="2026-03-10T08:00:00Z",
        record_key="MAGENE_A.fit",
    )

    parts = fp.split("|")
    assert parts[0] == "MAGENE_A.fit"
    assert len(parts[1]) == 64
    assert parts[2] == "2026-03-10T08:00:00Z"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_dedupe_service.py::test_fingerprint_uses_record_key_hash_and_start_time -v`

Expected: FAIL due to old function signature.

**Step 3: Write minimal implementation**

Update `make_fingerprint` signature and format:

```python
def make_fingerprint(path: Path, start_time: str, record_key: str) -> str:
    file_hash = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return f"{record_key}|{file_hash}|{start_time}"
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_dedupe_service.py::test_fingerprint_uses_record_key_hash_and_start_time -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_dedupe_service.py src/sync_onelap_strava/dedupe_service.py
git commit -m "feat: include record key in dedupe fingerprint"
```

### Task 4: Update SyncEngine for record-level flow

**Files:**
- Modify: `src/sync_onelap_strava/sync_engine.py`
- Test: `tests/test_sync_engine.py`

**Step 1: Write failing test for same activity two records**

Add to `tests/test_sync_engine.py`:

```python
def test_sync_engine_handles_two_records_same_activity_id(tmp_path):
    class FakeItem:
        def __init__(self, activity_id, start_time, record_key):
            self.activity_id = activity_id
            self.start_time = start_time
            self.record_key = record_key

    class FakeOnelap:
        def list_fit_activities(self, since, limit):
            return [
                FakeItem("677767", "2026-03-12T08:00:00Z", "MAGENE_A.fit"),
                FakeItem("677767", "2026-03-12T09:00:00Z", "MAGENE_B.fit"),
            ]

        def download_fit(self, record_key, output_dir):
            path = Path(output_dir) / record_key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(record_key.encode("utf-8"))
            return path

    class FakeState:
        def __init__(self):
            self.synced = {"MAGENE_A.fit|dummyhash|2026-03-12T08:00:00Z"}

        def is_synced(self, fingerprint):
            return fingerprint in self.synced

        def mark_synced(self, fingerprint, strava_activity_id):
            self.synced.add(fingerprint)

    class FakeStrava:
        def upload_fit(self, path):
            return 1

        def poll_upload(self, upload_id):
            return {"status": "ready", "error": None, "activity_id": 99}

    def fake_make_fingerprint(path, start_time, record_key):
        if record_key == "MAGENE_A.fit":
            return "MAGENE_A.fit|dummyhash|2026-03-12T08:00:00Z"
        return "MAGENE_B.fit|dummyhash|2026-03-12T09:00:00Z"

    engine = SyncEngine(FakeOnelap(), FakeStrava(), FakeState(), fake_make_fingerprint, tmp_path)
    summary = engine.run_once(since_date="2026-03-12", limit=50)

    assert summary.fetched == 2
    assert summary.deduped == 1
    assert summary.success == 1
    assert summary.failed == 0
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sync_engine.py::test_sync_engine_handles_two_records_same_activity_id -v`

Expected: FAIL due to old download/fingerprint call signatures.

**Step 3: Write minimal implementation**

In `src/sync_onelap_strava/sync_engine.py`:
- call `download_fit(item.record_key, self.download_dir)`
- call `make_fingerprint(fit_path, item.start_time, item.record_key)`
- keep current success/failure semantics for non-duplicate errors.

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_sync_engine.py -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_sync_engine.py src/sync_onelap_strava/sync_engine.py
git commit -m "feat: run sync pipeline with record-level keys"
```

### Task 5: Reclassify Strava duplicate response as deduped

**Files:**
- Modify: `src/sync_onelap_strava/sync_engine.py`
- Test: `tests/test_sync_engine.py`

**Step 1: Write failing test**

Add to `tests/test_sync_engine.py`:

```python
def test_sync_engine_counts_strava_duplicate_as_deduped_and_marks_state(tmp_path):
    class FakeItem:
        activity_id = "677767"
        start_time = "2026-03-12T08:00:00Z"
        record_key = "MAGENE_A.fit"

    class FakeOnelap:
        def list_fit_activities(self, since, limit):
            return [FakeItem()]

        def download_fit(self, record_key, output_dir):
            path = Path(output_dir) / record_key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fit")
            return path

    class FakeState:
        def __init__(self):
            self.marked = []

        def is_synced(self, fingerprint):
            return False

        def mark_synced(self, fingerprint, strava_activity_id):
            self.marked.append((fingerprint, strava_activity_id))

    class FakeStrava:
        def upload_fit(self, path):
            return 123

        def poll_upload(self, upload_id):
            return {
                "status": "There was an error processing your activity.",
                "error": "677767.fit duplicate of <a href='/activities/17696883248'>x</a>",
                "activity_id": None,
            }

    def fake_make_fingerprint(path, start_time, record_key):
        return "MAGENE_A.fit|hash|2026-03-12T08:00:00Z"

    state = FakeState()
    engine = SyncEngine(FakeOnelap(), FakeStrava(), state, fake_make_fingerprint, tmp_path)
    summary = engine.run_once(since_date="2026-03-12", limit=50)

    assert summary.success == 0
    assert summary.deduped == 1
    assert summary.failed == 0
    assert len(state.marked) == 1
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sync_engine.py::test_sync_engine_counts_strava_duplicate_as_deduped_and_marks_state -v`

Expected: FAIL because duplicate currently increments `failed`.

**Step 3: Write minimal implementation**

In `src/sync_onelap_strava/sync_engine.py`:
- Add helper to detect duplicate errors (`"duplicate of" in error.lower()`).
- On duplicate:
  - increment `deduped`,
  - `mark_synced(fingerprint, parsed_or_fallback_activity_id)`,
  - continue loop without incrementing `failed`.

For `strava_activity_id` when duplicate has no activity_id:
- parse first numeric id from error string if available,
- else use `-1` as sentinel.

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_sync_engine.py -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_sync_engine.py src/sync_onelap_strava/sync_engine.py
git commit -m "fix: classify Strava duplicates as deduped"
```

### Task 6: Full regression verification

**Files:**
- Modify: `docs/reference/onelap-adapter-notes.md`

**Step 1: Add docs update for new record-level behavior**

Update `docs/reference/onelap-adapter-notes.md` to reflect:
- list returns file-level records with `record_key`,
- download uses record key and source filename priority,
- duplicate handling contributes to dedupe count.

**Step 2: Run targeted test suite**

Run:

```bash
python -m pytest tests/test_onelap_client.py tests/test_onelap_download.py tests/test_dedupe_service.py tests/test_sync_engine.py tests/test_cli_download_only.py -v
```

Expected: PASS.

**Step 3: Run CLI smoke check**

Run:

```bash
python run_sync.py --help
```

Expected: command help prints without error.

**Step 4: Commit verification/docs updates**

```bash
git add docs/reference/onelap-adapter-notes.md
git commit -m "docs: document record-level OneLap fit sync behavior"
```

**Step 5: Final status check**

Run: `git status --short`

Expected: clean tree (or only unrelated untracked files such as local `.env`/workspace artifacts).
