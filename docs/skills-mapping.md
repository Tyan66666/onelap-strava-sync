# Skills to Root Code Mapping

This repository no longer stores local `skills/` artifacts.

Standalone skill distribution repository:

- `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills`
- Skill root: `onelap-strava-sync/`

## Skill Artifact

- `onelap-strava-sync/SKILL.md` (in standalone skills repo)
- `onelap-strava-sync/references/commands.md` (in standalone skills repo)

## Entrypoint

- `src/sync_onelap_strava/cli.py`
- `run_sync.py` (compatibility wrapper)

## Runtime Modules

- `src/sync_onelap_strava/config.py`
- `src/sync_onelap_strava/onelap_auth_init.py`
- `src/sync_onelap_strava/onelap_client.py`
- `src/sync_onelap_strava/strava_client.py`
- `src/sync_onelap_strava/sync_engine.py`
- `src/sync_onelap_strava/state_store.py`

## Maintenance Rule

- Business logic changes must be made in root source files.
- The standalone skills repo is the distribution and discovery layer.

## Global CLI

- Console script: `onelap-sync`
- Defined in `pyproject.toml` under `[project.scripts]`.
