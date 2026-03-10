from sync_onelap_strava.config import load_settings


def test_default_lookback_days_is_3(monkeypatch):
    monkeypatch.delenv("DEFAULT_LOOKBACK_DAYS", raising=False)
    s = load_settings(cli_since=None)
    assert s.default_lookback_days == 3
