def test_download_only_mode_does_not_require_strava_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("ONELAP_USERNAME", "u")
    monkeypatch.setenv("ONELAP_PASSWORD", "p")
    monkeypatch.delenv("STRAVA_CLIENT_ID", raising=False)
    monkeypatch.delenv("STRAVA_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("STRAVA_REFRESH_TOKEN", raising=False)

    class FakeOneLapClient:
        def list_fit_activities(self, since, limit):
            class Item:
                activity_id = "a1"
                start_time = "2026-03-09T08:00:00Z"

            return [Item()]

        def download_fit(self, activity_id, output_dir):
            p = tmp_path / f"{activity_id}.fit"
            p.write_bytes(b"fit")
            return p

    import run_sync

    monkeypatch.setattr(
        run_sync,
        "OneLapClient",
        lambda base_url, username, password: FakeOneLapClient(),
    )

    code = run_sync.run_cli(["--download-only", "--since", "2026-03-01"])
    assert code == 0
