# Sync OneLap Strava Agent Skills Design

## Background

Current project code lives in the runtime repository, while skill artifacts are distributed separately. The desired workflow is to copy `onelap-strava-sync` into `~/.agents/skills/` and have the agent use it immediately without manual dependency setup.

## Goals

- Create a dedicated repository at `C:\Users\13247\Documents\Code Project\sync_onelap_strava_agent_skills`.
- Keep all runtime-required code for the skill inside the skill's `scripts/` directory.
- Support first-use automatic dependency setup in an isolated virtual environment.
- Avoid any hard runtime dependency on the original repository path.

## Non-Goals

- No attempt to share live imports from the original repo at runtime.
- No prebuilt binary packaging in this phase.
- No always-on background installer when skill directories appear.

## Chosen Approach

Use a standalone distribution repository with self-contained code and a lazy bootstrap installer.

- Repository is dedicated to skill distribution.
- Skill contains executable code under `scripts/`.
- `bootstrap.py` handles venv lifecycle and dependency installation at first invocation.
- Future updates use a sync script to copy refreshed runtime modules from the source repo.

## Repository and Skill Layout

Target repo root:

- `C:\Users\13247\Documents\Code Project\sync_onelap_strava_agent_skills`

Skill root:

- `onelap-strava-sync/`

Planned structure:

- `onelap-strava-sync/SKILL.md`
- `onelap-strava-sync/references/commands.md`
- `onelap-strava-sync/scripts/bootstrap.py`
- `onelap-strava-sync/scripts/requirements.txt`
- `onelap-strava-sync/scripts/run_sync.py`
- `onelap-strava-sync/scripts/sync_onelap_strava/*.py`
- `tools/sync_from_runtime.ps1` (repo-level helper)

## Runtime Lifecycle

### First Trigger

- Agent activates `SKILL.md`.
- Skill commands route to `scripts/bootstrap.py`.
- Bootstrap checks `~/.agents/venvs/onelap-strava-sync/`.
- If absent, it creates venv and installs `scripts/requirements.txt`.
- Bootstrap writes an install fingerprint (python version + requirements hash).
- Bootstrap executes `scripts/run_sync.py` within the venv.

### Subsequent Triggers

- If fingerprint matches, reuse existing venv directly.
- If dependency fingerprint changes, reinstall dependencies automatically.
- If environment is broken, allow one rebuild attempt with clear error output.

## Migration Scope

Copy runtime modules from current repo into skill scripts:

- `src/sync_onelap_strava/*.py` -> `onelap-strava-sync/scripts/sync_onelap_strava/*.py`
- `run_sync.py` -> `onelap-strava-sync/scripts/run_sync.py`

Generate a minimized skill-local dependency list from the existing requirements files.

## Sync and Maintenance

- Provide `tools/sync_from_runtime.ps1` to refresh skill code from source runtime repository.
- Include a smoke test command after sync to catch packaging breakages early.
- Keep source-of-truth logic in runtime repo for now, with explicit sync into distribution repo.

## Validation Criteria

The design is successful when all conditions hold:

- Copy `onelap-strava-sync/` to `~/.agents/skills/`.
- Agent discovers and activates skill without extra manual setup.
- First trigger auto-creates isolated venv and installs dependencies.
- Primary command modes run: `--onelap-auth-init`, `--strava-auth-init`, `--since`, `--download-only`.

## Risks and Mitigations

- Network unavailable on first install: return actionable bootstrap error and retry guidance.
- Python version changes: detect mismatch and rebuild venv.
- Dual-repo drift: use sync script and smoke test gate before release.
