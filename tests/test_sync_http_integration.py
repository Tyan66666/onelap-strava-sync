import hashlib
import json
from datetime import date

import responses

from sync_onelap_strava.dedupe_service import make_fingerprint
from sync_onelap_strava.onelap_client import OneLapClient
from sync_onelap_strava.state_store import JsonStateStore
from sync_onelap_strava.strava_client import StravaClient
from sync_onelap_strava.sync_engine import SyncEngine


@responses.activate
def test_run_once_real_adapters_uploads_unsynced_only(tmp_path):
    a1_start = "2026-03-08T08:00:00Z"
    a2_start = "2026-03-09T08:00:00Z"
    a1_fp = f"{hashlib.sha256(b'fit-a1').hexdigest()}|{a1_start}"

    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "synced": {
                    a1_fp: {
                        "strava_activity_id": 101,
                        "synced_at": "2026-03-10T00:00:00+00:00",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    responses.add(
        responses.POST,
        "https://www.onelap.cn/api/login",
        json={"code": 0},
        headers={"Set-Cookie": "sid=abc; Path=/"},
        status=200,
    )
    responses.add(
        responses.GET,
        "http://u.onelap.cn/analysis/list",
        json={"message": "unauthorized"},
        status=401,
    )
    responses.add(
        responses.GET,
        "http://u.onelap.cn/analysis/list",
        json={
            "data": [
                {"id": "a1", "start_time": a1_start, "fit_url": "/fit/a1.fit"},
                {"id": "a2", "start_time": a2_start, "fit_url": "/fit/a2.fit"},
            ]
        },
        status=200,
    )
    responses.add(
        responses.GET,
        "https://www.onelap.cn/fit/a1.fit",
        body=b"fit-a1",
        status=200,
        content_type="application/octet-stream",
    )
    responses.add(
        responses.GET,
        "https://www.onelap.cn/fit/a2.fit",
        body=b"fit-a2",
        status=200,
        content_type="application/octet-stream",
    )
    responses.add(
        responses.POST,
        "https://www.strava.com/api/v3/uploads",
        json={"id": 9001},
        status=201,
    )
    responses.add(
        responses.GET,
        "https://www.strava.com/api/v3/uploads/9001",
        json={"status": "ready", "error": None, "activity_id": 321},
        status=200,
    )

    engine = SyncEngine(
        onelap_client=OneLapClient(
            base_url="https://www.onelap.cn", username="u", password="p"
        ),
        strava_client=StravaClient(
            client_id="id",
            client_secret="secret",
            refresh_token="r",
            access_token="a",
            expires_at=9999999999,
        ),
        state_store=JsonStateStore(state_path),
        make_fingerprint=make_fingerprint,
        download_dir=tmp_path / "downloads",
    )

    summary = engine.run_once(since_date=date(2026, 3, 1), limit=50)

    assert summary.fetched == 2
    assert summary.deduped == 1
    assert summary.success == 1
    assert summary.failed == 0

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert len(state["synced"]) == 2
    a2_fp = f"{hashlib.sha256(b'fit-a2').hexdigest()}|{a2_start}"
    assert a2_fp in state["synced"]

    upload_calls = [
        c
        for c in responses.calls
        if c.request.url == "https://www.strava.com/api/v3/uploads"
    ]
    assert len(upload_calls) == 1

    login_calls = [
        c for c in responses.calls if c.request.url == "https://www.onelap.cn/api/login"
    ]
    assert len(login_calls) == 1
