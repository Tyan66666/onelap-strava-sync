from datetime import date

from sync_onelap_strava.onelap_client import OneLapClient


def test_list_fit_activities_after_since_date():
    class FakeBackend:
        def login(self):
            return True

        def list_fit_activities(self, limit):
            return [
                {"activity_id": "1", "start_time": "2026-03-06T08:00:00Z"},
                {"activity_id": "2", "start_time": "2026-03-07T09:00:00Z"},
                {"activity_id": "3", "start_time": "2026-03-10T07:00:00Z"},
            ]

    c = OneLapClient(FakeBackend())
    items = c.list_fit_activities(since=date(2026, 3, 7), limit=50)
    assert all(i.start_time >= "2026-03-07" for i in items)
