import time

import requests


class StravaClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        access_token: str,
        expires_at: int,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = access_token
        self.expires_at = expires_at

    def ensure_access_token(self) -> str:
        now = int(time.time())
        if self.access_token and self.expires_at > now:
            return self.access_token

        resp = requests.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        self.access_token = payload["access_token"]
        self.refresh_token = payload.get("refresh_token", self.refresh_token)
        self.expires_at = payload.get("expires_at", self.expires_at)
        return self.access_token
