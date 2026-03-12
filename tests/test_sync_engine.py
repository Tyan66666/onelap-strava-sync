import logging
from pathlib import Path

from sync_onelap_strava.sync_engine import SyncEngine


def test_sync_engine_uploads_only_unsynced_items(tmp_path):
    class FakeItem:
        def __init__(self, activity_id, start_time, record_key):
            self.activity_id = activity_id
            self.start_time = start_time
            self.record_key = record_key

    class FakeOnelap:
        def list_fit_activities(self, since, limit):
            return [
                FakeItem("a1", "2026-03-10T08:00:00Z", "rk-a1"),
                FakeItem("a2", "2026-03-10T09:00:00Z", "rk-a2"),
                FakeItem("a3", "2026-03-10T10:00:00Z", "rk-a3"),
            ]

        def download_fit(self, record_key, output_dir):
            path = Path(output_dir) / f"{record_key}.fit"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fit")
            return path

    class FakeState:
        def __init__(self):
            self.synced = {
                "rk-a1|hash-rk-a1|2026-03-10T08:00:00Z",
                "rk-a2|hash-rk-a2|2026-03-10T09:00:00Z",
            }

        def is_synced(self, fingerprint):
            return fingerprint in self.synced

        def mark_synced(self, fingerprint, strava_activity_id):
            self.synced.add(fingerprint)

    class FakeStrava:
        def __init__(self):
            self.upload_calls = 0

        def upload_fit(self, path):
            self.upload_calls += 1
            return 11

        def poll_upload(self, upload_id):
            return {"status": "ready", "error": None, "activity_id": 99}

    def fake_make_fingerprint(path, start_time, record_key):
        name = Path(path).stem
        return f"{record_key}|hash-{name}|{start_time}"

    engine = SyncEngine(
        onelap_client=FakeOnelap(),
        strava_client=FakeStrava(),
        state_store=FakeState(),
        make_fingerprint=fake_make_fingerprint,
        download_dir=tmp_path,
    )

    summary = engine.run_once(since_date="2026-03-07", limit=50)

    assert summary.fetched == 3
    assert summary.deduped == 2
    assert summary.success == 1
    assert summary.failed == 0
    assert engine.strava_client.upload_calls == 1


def test_sync_engine_logs_poll_error_details(tmp_path, caplog):
    class FakeItem:
        def __init__(self, activity_id, start_time, record_key):
            self.activity_id = activity_id
            self.start_time = start_time
            self.record_key = record_key

    class FakeOnelap:
        def list_fit_activities(self, since, limit):
            return [FakeItem("a1", "2026-03-10T08:00:00Z", "rk-a1")]

        def download_fit(self, record_key, output_dir):
            path = Path(output_dir) / f"{record_key}.fit"
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
                "error": "file parse failed",
                "activity_id": None,
            }

    def fake_make_fingerprint(path, start_time, record_key):
        return f"{record_key}|fp|{start_time}"

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
    assert "file parse failed" in caplog.text
    assert "a1" in caplog.text


def test_sync_engine_logs_exception_message_when_upload_raises(tmp_path, caplog):
    class FakeItem:
        def __init__(self, activity_id, start_time, record_key):
            self.activity_id = activity_id
            self.start_time = start_time
            self.record_key = record_key

    class FakeOnelap:
        def list_fit_activities(self, since, limit):
            return [FakeItem("a1", "2026-03-10T08:00:00Z", "rk-a1")]

        def download_fit(self, record_key, output_dir):
            path = Path(output_dir) / f"{record_key}.fit"
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

    def fake_make_fingerprint(path, start_time, record_key):
        return f"{record_key}|fp|{start_time}"

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

    engine = SyncEngine(
        FakeOnelap(), FakeStrava(), FakeState(), fake_make_fingerprint, tmp_path
    )
    summary = engine.run_once(since_date="2026-03-12", limit=50)

    assert summary.fetched == 2
    assert summary.deduped == 1
    assert summary.success == 1
    assert summary.failed == 0


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
    engine = SyncEngine(
        FakeOnelap(), FakeStrava(), state, fake_make_fingerprint, tmp_path
    )
    summary = engine.run_once(since_date="2026-03-12", limit=50)

    assert summary.success == 0
    assert summary.deduped == 1
    assert summary.failed == 0
    assert len(state.marked) == 1
    assert state.marked[0][1] == 17696883248
