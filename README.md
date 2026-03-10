# OneLap to Strava Sync

Local one-command Python tool to export FIT files from OneLap and incrementally upload to Strava.

## Setup

1. Create and activate virtual environment.
2. Install dependencies:
   - `pip install -r requirements-dev.txt`
3. Copy `.env.example` to `.env` and fill required values.

## OAuth First Run

1. Create Strava API app and get `client_id` + `client_secret`.
2. Complete an OAuth authorization flow to obtain `refresh_token`.
3. Save credentials in `.env`.

## One-command Run

- Default lookback run:
  - `python run_sync.py`
- Run with explicit start date:
  - `python run_sync.py --since 2026-03-01`

## --since Usage

- Use ISO date format: `YYYY-MM-DD`
- Example: `python run_sync.py --since 2026-03-01`

## Troubleshooting

- If import errors happen, confirm dependencies are installed in the active virtual environment.
- If Strava upload fails with 5xx, rerun; retriable errors use bounded backoff.
- If OneLap risk control triggers, wait and rerun later.
