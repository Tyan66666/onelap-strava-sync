def test_run_cli_returns_nonzero_on_missing_required_settings(monkeypatch):
    monkeypatch.setenv("ONELAP_USERNAME", "")
    monkeypatch.setenv("ONELAP_PASSWORD", "")
    monkeypatch.setenv("STRAVA_CLIENT_ID", "")
    monkeypatch.setenv("STRAVA_CLIENT_SECRET", "")
    monkeypatch.setenv("STRAVA_REFRESH_TOKEN", "")

    from run_sync import run_cli

    code = run_cli([])
    assert code != 0
