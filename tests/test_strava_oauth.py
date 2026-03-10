import responses

from sync_onelap_strava.strava_client import StravaClient


@responses.activate
def test_refresh_token_called_when_access_token_expired(tmp_path):
    responses.add(
        responses.POST,
        "https://www.strava.com/oauth/token",
        json={
            "access_token": "new-token",
            "refresh_token": "new-refresh",
            "expires_at": 9999999999,
        },
        status=200,
    )
    client = StravaClient(
        client_id="id",
        client_secret="secret",
        refresh_token="old",
        access_token="expired",
        expires_at=0,
    )
    token = client.ensure_access_token()
    assert token == "new-token"
