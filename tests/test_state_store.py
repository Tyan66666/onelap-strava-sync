from sync_onelap_strava.state_store import JsonStateStore


def test_add_and_check_synced_record(tmp_path):
    store = JsonStateStore(tmp_path / "state.json")
    fp = "abc123|2026-03-10T08:00:00Z"
    assert not store.is_synced(fp)
    store.mark_synced(fp, strava_activity_id=42)
    assert store.is_synced(fp)
