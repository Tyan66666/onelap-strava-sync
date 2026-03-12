from sync_onelap_strava.sync_engine import SyncSummary


def test_cli_accepts_since_argument_and_prints_summary(capsys):
    class FakeEngine:
        def run_once(self, since_date=None, limit=50):
            assert str(since_date) == "2026-03-01"
            return SyncSummary(fetched=5, deduped=2, success=2, failed=1)

    from run_sync import run_cli

    exit_code = run_cli(["--since", "2026-03-01"], engine=FakeEngine())
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "fetched 5 -> deduped 2 -> success 2 -> failed 1" in out


def test_run_sync_script_help_exits_zero():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "run_sync.py", "--help"], capture_output=True, text=True
    )

    assert result.returncode == 0
    assert "--since" in result.stdout


def test_build_default_engine_uses_real_clients(monkeypatch):
    monkeypatch.setenv("ONELAP_USERNAME", "u")
    monkeypatch.setenv("ONELAP_PASSWORD", "p")
    monkeypatch.setenv("STRAVA_CLIENT_ID", "id")
    monkeypatch.setenv("STRAVA_CLIENT_SECRET", "secret")
    monkeypatch.setenv("STRAVA_REFRESH_TOKEN", "r")
    monkeypatch.setenv("STRAVA_ACCESS_TOKEN", "a")
    monkeypatch.setenv("STRAVA_EXPIRES_AT", "123")

    from run_sync import build_default_engine

    engine = build_default_engine()
    assert engine.onelap_client.__class__.__name__ == "OneLapClient"
    assert engine.strava_client.__class__.__name__ == "StravaClient"


def test_cli_accepts_download_only_argument_and_runs_engine(capsys):
    class FakeEngine:
        def run_once(self, since_date=None, limit=50):
            return SyncSummary(fetched=0, deduped=0, success=0, failed=0)

    from run_sync import run_cli

    exit_code = run_cli(["--download-only"], engine=FakeEngine())
    assert exit_code == 0


def test_cli_runs_strava_auth_init_and_exits_zero(monkeypatch):
    monkeypatch.setenv("STRAVA_CLIENT_ID", "210500")
    monkeypatch.setenv("STRAVA_CLIENT_SECRET", "secret")

    called = {"ok": False}

    def fake_run_strava_auth_init(client_id, client_secret, env_file):
        assert client_id == "210500"
        assert client_secret == "secret"
        called["ok"] = True

    import run_sync

    monkeypatch.setattr(run_sync, "run_strava_auth_init", fake_run_strava_auth_init)

    code = run_sync.run_cli(["--strava-auth-init"])
    assert code == 0
    assert called["ok"]


def test_package_cli_module_accepts_since_argument_and_prints_summary(capsys):
    class FakeEngine:
        def run_once(self, since_date=None, limit=50):
            assert str(since_date) == "2026-03-01"
            return SyncSummary(fetched=3, deduped=1, success=1, failed=1)

    from sync_onelap_strava.cli import run_cli

    exit_code = run_cli(["--since", "2026-03-01"], engine=FakeEngine())
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "fetched 3 -> deduped 1 -> success 1 -> failed 1" in out
