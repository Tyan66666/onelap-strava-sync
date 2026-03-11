from datetime import date

import responses

from sync_onelap_strava.onelap_client import OneLapClient


@responses.activate
def test_list_fit_activities_filters_since_date():
    responses.add(
        responses.GET,
        "http://u.onelap.cn/analysis/list",
        json={
            "data": [
                {
                    "id": "a1",
                    "start_time": "2026-03-06T08:00:00Z",
                    "fit_url": "/fit/a1.fit",
                },
                {
                    "id": "a2",
                    "start_time": "2026-03-08T08:00:00Z",
                    "fit_url": "/fit/a2.fit",
                },
            ]
        },
        status=200,
    )
    c = OneLapClient(base_url="https://www.onelap.cn", username="u", password="p")
    items = c.list_fit_activities(since=date(2026, 3, 7), limit=50)
    assert [i.activity_id for i in items] == ["a2"]


@responses.activate
def test_list_fit_activities_uses_u_onelap_analysis_list_endpoint():
    responses.add(
        responses.GET,
        "http://u.onelap.cn/analysis/list",
        json={
            "data": [
                {
                    "id": "a2",
                    "start_time": "2026-03-08T08:00:00Z",
                    "fit_url": "/fit/a2.fit",
                }
            ]
        },
        status=200,
    )

    c = OneLapClient(base_url="https://www.onelap.cn", username="u", password="p")
    items = c.list_fit_activities(since=date(2026, 3, 7), limit=50)

    assert [i.activity_id for i in items] == ["a2"]


@responses.activate
def test_list_fit_activities_supports_created_at_and_durl_fields():
    responses.add(
        responses.GET,
        "http://u.onelap.cn/analysis/list",
        json={
            "data": [
                {
                    "id": "a2",
                    "created_at": 1772956800,
                    "durl": "/fit/a2.fit",
                }
            ]
        },
        status=200,
    )

    c = OneLapClient(base_url="https://www.onelap.cn", username="u", password="p")
    items = c.list_fit_activities(since=date(2026, 3, 1), limit=50)

    assert [i.activity_id for i in items] == ["a2"]
    assert items[0].fit_url == "/fit/a2.fit"


@responses.activate
def test_list_fit_activities_retries_after_redirect_to_login():
    responses.add(
        responses.GET,
        "http://u.onelap.cn/analysis/list",
        body="<html>login</html>",
        status=200,
        content_type="text/html",
    )
    responses.add(
        responses.POST,
        "https://www.onelap.cn/api/login",
        json={"code": 0},
        status=200,
    )
    responses.add(
        responses.GET,
        "http://u.onelap.cn/analysis/list",
        json={
            "data": [
                {
                    "id": "a2",
                    "start_time": "2026-03-08T08:00:00Z",
                    "fit_url": "/fit/a2.fit",
                }
            ]
        },
        status=200,
    )

    c = OneLapClient(base_url="https://www.onelap.cn", username="u", password="p")
    items = c.list_fit_activities(since=date(2026, 3, 7), limit=50)

    assert [i.activity_id for i in items] == ["a2"]
