import responses

from sync_onelap_strava.onelap_client import OneLapClient


@responses.activate
def test_onelap_login_stores_session_cookie():
    responses.add(
        responses.POST,
        "https://www.onelap.cn/api/login",
        json={"code": 0},
        headers={"Set-Cookie": "sid=abc; Path=/"},
        status=200,
    )
    client = OneLapClient(base_url="https://www.onelap.cn", username="u", password="p")
    client.login()
    assert client.session.cookies.get("sid") == "abc"


@responses.activate
def test_onelap_login_treats_code_200_as_success():
    responses.add(
        responses.POST,
        "https://www.onelap.cn/api/login",
        json={"code": 200, "error": "success"},
        headers={"Set-Cookie": "sid=ok; Path=/"},
        status=200,
    )

    client = OneLapClient(base_url="https://www.onelap.cn", username="u", password="p")
    client.login()
    assert client.session.cookies.get("sid") == "ok"
