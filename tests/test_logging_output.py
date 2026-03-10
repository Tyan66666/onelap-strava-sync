from pathlib import Path

from sync_onelap_strava.sync_engine import SyncSummary


def test_run_creates_log_file_with_summary(tmp_path):
    from run_sync import run_cli

    class FakeEngine:
        def run_once(self, since_date=None, limit=50):
            return SyncSummary(fetched=8, deduped=3, success=3, failed=0)

    log_file = Path(tmp_path) / "logs" / "sync.log"
    exit_code = run_cli([], engine=FakeEngine(), log_file=log_file)

    assert exit_code == 0
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "success=3" in content
    assert "failed=0" in content
