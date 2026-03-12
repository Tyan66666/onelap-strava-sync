# OneLap Adapter Notes

`OneLapClient` now uses direct OneLap HTTP APIs (no placeholder backend):

- `login()` -> POST `https://www.onelap.cn/login` and stores session cookie
- `list_fit_activities(since, limit)` -> GET `http://u.onelap.cn/analysis/list`, normalizes to file-level `OneLapActivity`, applies since-date filter, caches `fit_url` by `record_key`
- `download_fit(record_key, output_dir)` -> downloads cached `fit_url` to `<output_dir>/<source_filename>`, sanitizes names, and avoids overwrite collisions

Runtime behavior notes:

- On first list request, 401 triggers one login attempt and retry.
- `SyncEngine` remains responsible for dedupe/state transitions and Strava upload flow.
- Dedupe fingerprint is file-level (`record_key|sha256|start_time`) so same `activity_id` with different FIT files does not collapse.
- Strava `duplicate of ...` responses are classified as deduped and written to state to avoid repeated retries.
