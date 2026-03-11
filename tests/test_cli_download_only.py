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


def test_download_only_prints_one_line_per_fit_with_time_and_filename(
    monkeypatch, capsys
):
    monkeypatch.setenv("ONELAP_USERNAME", "u")
    monkeypatch.setenv("ONELAP_PASSWORD", "p")

    class Item:
        def __init__(self, activity_id, start_time):
            self.activity_id = activity_id
            self.start_time = start_time

    class FakeOneLapClient:
        def list_fit_activities(self, since, limit):
            return [
                Item("a1", "2026-03-08T08:00:00Z"),
                Item("a2", "2026-03-09T08:00:00Z"),
            ]

        def download_fit(self, activity_id, output_dir):
            from pathlib import Path

            p = Path(output_dir) / f"{activity_id}.fit"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"fit")
            return p

    import run_sync

    monkeypatch.setattr(
        run_sync,
        "OneLapClient",
        lambda base_url, username, password: FakeOneLapClient(),
    )

    code = run_sync.run_cli(["--download-only", "--since", "2026-03-01"])
    out = capsys.readouterr().out

    assert code == 0
    assert "2026-03-08T08:00:00Z  a1.fit" in out
    assert "2026-03-09T08:00:00Z  a2.fit" in out
    assert "download-only fetched 2 -> downloaded 2 -> failed 0" in out


def test_download_only_prints_failed_line_for_item_errors(monkeypatch, capsys):
    monkeypatch.setenv("ONELAP_USERNAME", "u")
    monkeypatch.setenv("ONELAP_PASSWORD", "p")

    class Item:
        def __init__(self, activity_id, start_time):
            self.activity_id = activity_id
            self.start_time = start_time

    class FakeOneLapClient:
        def list_fit_activities(self, since, limit):
            return [Item("a1", "2026-03-08T08:00:00Z")]

        def download_fit(self, activity_id, output_dir):
            raise RuntimeError("disk full")

    import run_sync

    monkeypatch.setattr(
        run_sync,
        "OneLapClient",
        lambda base_url, username, password: FakeOneLapClient(),
    )

    code = run_sync.run_cli(["--download-only", "--since", "2026-03-01"])
    out = capsys.readouterr().out

    assert code == 0
    assert "2026-03-08T08:00:00Z  a1.fit  FAILED: disk full" in out
    assert "download-only fetched 1 -> downloaded 0 -> failed 1" in out


def test_download_only_returns_nonzero_when_onelap_settings_missing(monkeypatch):
    monkeypatch.setenv("ONELAP_USERNAME", "")
    monkeypatch.setenv("ONELAP_PASSWORD", "")

    from run_sync import run_cli

    code = run_cli(["--download-only"])
    assert code != 0
