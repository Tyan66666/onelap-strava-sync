from pathlib import Path

import responses

from sync_onelap_strava.sync_engine import SyncEngine


def test_onelap_risk_control_stops_current_run(tmp_path):
    from sync_onelap_strava.sync_engine import OnelapRiskControlError

    class FakeOnelap:
        def list_fit_activities(self, since, limit):
            raise OnelapRiskControlError("risk-control")

        def download_fit(self, activity_id, output_dir):
            raise AssertionError("should not be called")

    class FakeState:
        def is_synced(self, fingerprint):
            return False

        def mark_synced(self, fingerprint, strava_activity_id):
            pass

    class FakeStrava:
        def upload_fit(self, path):
            raise AssertionError("should not be called")

        def poll_upload(self, upload_id):
            raise AssertionError("should not be called")

    engine = SyncEngine(
        onelap_client=FakeOnelap(),
        strava_client=FakeStrava(),
        state_store=FakeState(),
        make_fingerprint=lambda path, start_time: "x",
        download_dir=tmp_path,
    )

    summary = engine.run_once(since_date="2026-03-01", limit=50)

    assert summary.aborted_reason == "risk-control"
    assert summary.fetched == 0


@responses.activate
def test_strava_5xx_uses_backoff_then_succeeds(tmp_path):
    from sync_onelap_strava.strava_client import StravaClient

    client = StravaClient(
        client_id="id",
        client_secret="secret",
        refresh_token="refresh",
        access_token="token",
        expires_at=9999999999,
    )

    fit_file = Path(tmp_path) / "x.fit"
    fit_file.write_bytes(b"fit")

    responses.add(
        responses.POST,
        "https://www.strava.com/api/v3/uploads",
        json={"message": "server error"},
        status=500,
    )
    responses.add(
        responses.POST,
        "https://www.strava.com/api/v3/uploads",
        json={"id": 789},
        status=201,
    )

    upload_id = client.upload_fit(fit_file, retries=2, backoff_seconds=0)
    assert upload_id == 789
