# OneLap Adapter Notes

`OneLapClient` wraps backend methods from the existing OneLap integration class (`SyncOnelapToXoss`-style API):

- `login()` -> delegates to backend `login()`
- `list_fit_activities(since, limit)` -> delegates to backend `list_fit_activities(limit=...)` and applies since-date filter in adapter
- `download_fit(activity_id, output_dir)` -> delegates to backend `download_fit(...)`

The adapter keeps orchestration logic out of backend code so sync engine can stay framework-agnostic.
