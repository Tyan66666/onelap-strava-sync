# OneLap to Strava Sync

中文名：OneLap 同步 Strava

## Purpose

Use this skill to run OneLap to Strava sync workflows through the existing root CLI.

## Trigger

- User asks to sync OneLap FIT files to Strava.
- User asks to download OneLap FIT files without upload.
- User asks to initialize Strava OAuth tokens.

## Usage

See `resources/commands.md` for exact commands.

Prefer the global command `onelap-sync` (installed from package `onelap-strava-sync`).

## Notes

- Source of truth stays in root code (`run_sync.py`, `src/sync_onelap_strava`).
- This skill is a distribution layer and does not duplicate business logic.
