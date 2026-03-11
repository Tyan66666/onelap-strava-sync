from sync_onelap_strava.sync_engine import SyncSummary
from pathlib import Path


def test_e2e_dry_run_report_format(capsys):
    from run_sync import run_cli

    class FakeEngine:
        def run_once(self, since_date=None, limit=50):
            return SyncSummary(fetched=8, deduped=3, success=3, failed=0)

    exit_code = run_cli([], engine=FakeEngine())
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "fetched 8 -> deduped 3 -> success 3 -> failed 0" in out


def test_user_docs_and_env_example_exist():
    readme = Path("README.md")
    env_example = Path(".env.example")

    assert readme.exists()
    assert env_example.exists()

    readme_text = readme.read_text(encoding="utf-8")
    assert "## Setup" in readme_text
    assert "## OAuth First Run" in readme_text
    assert "## One-command Run" in readme_text
    assert "## Troubleshooting" in readme_text

    env_text = env_example.read_text(encoding="utf-8")
    assert "STRAVA_CLIENT_ID=" in env_text
    assert "STRAVA_CLIENT_SECRET=" in env_text
    assert "STRAVA_REFRESH_TOKEN=" in env_text


def test_readme_documents_real_onelap_http_usage():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "OneLap HTTP" in text


def test_readme_documents_download_only_mode():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "--download-only" in text
    assert "download-only fetched" in text
