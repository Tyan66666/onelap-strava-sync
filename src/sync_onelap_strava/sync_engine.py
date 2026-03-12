import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


LOGGER = logging.getLogger("sync_onelap_strava")


class OnelapRiskControlError(Exception):
    pass


@dataclass
class SyncSummary:
    fetched: int
    deduped: int
    success: int
    failed: int
    aborted_reason: str | None = None


class SyncEngine:
    def __init__(
        self,
        onelap_client,
        strava_client,
        state_store,
        make_fingerprint,
        download_dir: Path,
    ):
        self.onelap_client = onelap_client
        self.strava_client = strava_client
        self.state_store = state_store
        self.make_fingerprint = make_fingerprint
        self.download_dir = Path(download_dir)

    def run_once(self, since_date=None, limit: int = 50) -> SyncSummary:
        if since_date is None:
            since_value = date.today() - timedelta(days=3)
        elif isinstance(since_date, str):
            since_value = date.fromisoformat(since_date)
        else:
            since_value = since_date

        try:
            items = self.onelap_client.list_fit_activities(
                since=since_value, limit=limit
            )
        except OnelapRiskControlError:
            return SyncSummary(
                fetched=0,
                deduped=0,
                success=0,
                failed=0,
                aborted_reason="risk-control",
            )
        fetched = len(items)
        deduped = 0
        success = 0
        failed = 0

        for item in items:
            fit_path = self.onelap_client.download_fit(
                item.record_key, self.download_dir
            )
            fingerprint = self.make_fingerprint(
                fit_path, item.start_time, item.record_key
            )
            if self.state_store.is_synced(fingerprint):
                deduped += 1
                continue

            try:
                upload_id = self.strava_client.upload_fit(fit_path)
                result = self.strava_client.poll_upload(upload_id)
                activity_id = result.get("activity_id")
                if activity_id is None or result.get("error") is not None:
                    if self._is_duplicate_error(result.get("error")):
                        duplicate_activity_id = self._extract_duplicate_activity_id(
                            result.get("error")
                        )
                        self.state_store.mark_synced(
                            fingerprint,
                            duplicate_activity_id
                            if duplicate_activity_id is not None
                            else -1,
                        )
                        deduped += 1
                        continue
                    LOGGER.error(
                        "strava upload failed activity_id=%s upload_id=%s status=%s error=%s",
                        item.activity_id,
                        upload_id,
                        result.get("status"),
                        result.get("error"),
                    )
                    failed += 1
                    continue
                self.state_store.mark_synced(fingerprint, int(activity_id))
                success += 1
            except Exception as exc:
                LOGGER.error(
                    "strava upload exception activity_id=%s error=%s",
                    item.activity_id,
                    exc,
                )
                failed += 1

        return SyncSummary(
            fetched=fetched, deduped=deduped, success=success, failed=failed
        )

    def _is_duplicate_error(self, error: object) -> bool:
        return "duplicate of" in str(error or "").lower()

    def _extract_duplicate_activity_id(self, error: object) -> int | None:
        text = str(error or "")
        match = re.search(r"/activities/(\d+)", text)
        if not match:
            match = re.search(r"activity\s+(\d+)", text, flags=re.IGNORECASE)
        if not match:
            return None
        return int(match.group(1))
