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
