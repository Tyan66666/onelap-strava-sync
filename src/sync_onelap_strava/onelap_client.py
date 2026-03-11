from dataclasses import dataclass
from datetime import UTC, date, datetime
import hashlib
from pathlib import Path

import requests


@dataclass
class OneLapActivity:
    activity_id: str
    start_time: str
    fit_url: str


class OneLapClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._activity_fit_urls: dict[str, str] = {}

    def login(self):
        request_data = {
            "account": self.username,
            "password": hashlib.md5(self.password.encode("utf-8")).hexdigest(),
        }
        response = self.session.post(
            f"{self.base_url}/api/login",
            data=request_data,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") not in {0, 200}:
            raise RuntimeError(
                f"OneLap login failed: {payload.get('error', 'unknown')}"
            )
        return True

    def list_fit_activities(self, since: date, limit: int):
        payload = self._fetch_activities_payload()
        items = payload.get("data", [])
        cutoff = since.isoformat()
        result: list[OneLapActivity] = []

        for raw in items:
            activity_id = str(raw.get("id") or raw.get("activity_id") or "")
            start_time = self._parse_start_time(raw)
            fit_url = str(
                raw.get("fit_url") or raw.get("durl") or raw.get("fitUrl") or ""
            )
            if not activity_id or not start_time or not fit_url:
                continue
            if start_time[:10] < cutoff:
                continue

            normalized = OneLapActivity(
                activity_id=activity_id,
                start_time=start_time,
                fit_url=fit_url,
            )
            self._activity_fit_urls[activity_id] = fit_url
            result.append(normalized)
            if len(result) >= limit:
                break

        return result

    def _fetch_activities_payload(self) -> dict:
        for attempt in range(2):
            response = self.session.get("http://u.onelap.cn/analysis/list", timeout=30)
            if self._requires_login(response):
                if attempt == 1:
                    raise RuntimeError("OneLap activities request requires login")
                self.login()
                continue

            response.raise_for_status()
            try:
                payload = response.json()
            except ValueError:
                if attempt == 1:
                    raise RuntimeError("OneLap activities response is not JSON")
                self.login()
                continue

            if isinstance(payload, dict):
                return payload
            if attempt == 1:
                raise RuntimeError("OneLap activities payload is invalid")
            self.login()

        raise RuntimeError("failed to fetch OneLap activities")

    def _requires_login(self, response: requests.Response) -> bool:
        if response.status_code in {401, 403}:
            return True

        content_type = (response.headers.get("Content-Type") or "").lower()
        if "text/html" in content_type:
            return True

        return "login.html" in response.url

    def _parse_start_time(self, raw: dict) -> str:
        value = raw.get("start_time")
        if value:
            return str(value)

        created_at = raw.get("created_at")
        if isinstance(created_at, int):
            return datetime.fromtimestamp(created_at, UTC).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        if isinstance(created_at, str):
            if created_at.isdigit():
                return datetime.fromtimestamp(int(created_at), UTC).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
            return created_at
        return ""

    def download_fit(self, activity_id: str, output_dir: Path):
        fit_url = self._activity_fit_urls.get(activity_id)
        if not fit_url:
            raise RuntimeError(f"missing fit_url for activity {activity_id}")

        if fit_url.startswith("http://") or fit_url.startswith("https://"):
            download_url = fit_url
        else:
            download_url = f"{self.base_url}/{fit_url.lstrip('/')}"

        response = self.session.get(download_url, stream=True, timeout=30)
        response.raise_for_status()

        output_path = Path(output_dir) / f"{activity_id}.fit"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    handle.write(chunk)

        return output_path
