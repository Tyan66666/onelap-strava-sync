from dataclasses import dataclass
from datetime import date


@dataclass
class Settings:
    default_lookback_days: int
    cli_since: date | None


def load_settings(cli_since):
    return Settings(default_lookback_days=3, cli_since=cli_since)
