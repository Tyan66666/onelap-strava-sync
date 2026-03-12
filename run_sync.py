import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import sync_onelap_strava.cli as _cli

OneLapClient = _cli.OneLapClient
run_strava_auth_init = _cli.run_strava_auth_init


def _sync_runtime_overrides():
    _cli.OneLapClient = OneLapClient
    _cli.run_strava_auth_init = run_strava_auth_init


def build_default_engine():
    _sync_runtime_overrides()
    return _cli.build_default_engine()


def run_download_only(since_value):
    _sync_runtime_overrides()
    return _cli.run_download_only(since_value)


def run_cli(argv=None, engine=None, log_file: Path | str = "logs/sync.log"):
    _sync_runtime_overrides()
    return _cli.run_cli(argv=argv, engine=engine, log_file=log_file)


def main():
    raise SystemExit(run_cli())


if __name__ == "__main__":
    main()
