from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass
class OneLapActivity:
    activity_id: str
    start_time: str


class OneLapClient:
    def __init__(self, backend):
        self.backend = backend

    def login(self):
        return self.backend.login()

    def list_fit_activities(self, since: date, limit: int):
        items = self.backend.list_fit_activities(limit=limit)
        cutoff = since.isoformat()
        filtered = []
        for item in items:
            if item["start_time"][:10] >= cutoff:
                filtered.append(
                    OneLapActivity(
                        activity_id=str(item["activity_id"]),
                        start_time=str(item["start_time"]),
                    )
                )
        return filtered

    def download_fit(self, activity_id: str, output_dir: Path):
        return self.backend.download_fit(activity_id=activity_id, output_dir=output_dir)
