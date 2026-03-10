import json
from datetime import datetime, timezone
from pathlib import Path


class JsonStateStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def _load(self) -> dict:
        if not self.path.exists():
            return {"synced": {}}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if "synced" not in data:
            data["synced"] = {}
        return data

    def _save(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def is_synced(self, fingerprint: str) -> bool:
        data = self._load()
        return fingerprint in data["synced"]

    def mark_synced(self, fingerprint: str, strava_activity_id: int) -> None:
        data = self._load()
        data["synced"][fingerprint] = {
            "strava_activity_id": strava_activity_id,
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save(data)

    def last_success_sync_time(self) -> str | None:
        data = self._load()
        synced = data.get("synced", {})
        if not synced:
            return None
        latest = max(item["synced_at"] for item in synced.values())
        return latest
