# Skills to Root Code Mapping

## Skill Artifact

- `skills/onelap-strava-sync/SKILL.md`
- `skills/onelap-strava-sync/resources/commands.md`

## Entrypoint

- `src/sync_onelap_strava/cli.py`
- `run_sync.py` (compatibility wrapper)

## Runtime Modules

- `src/sync_onelap_strava/config.py`
- `src/sync_onelap_strava/onelap_client.py`
- `src/sync_onelap_strava/strava_client.py`
- `src/sync_onelap_strava/sync_engine.py`
- `src/sync_onelap_strava/state_store.py`

## Maintenance Rule

- Business logic changes must be made in root source files.
- The `skills/` directory is a distribution and discovery layer.

## Global CLI

- Console script: `onelap-sync`
- Defined in `pyproject.toml` under `[project.scripts]`.
