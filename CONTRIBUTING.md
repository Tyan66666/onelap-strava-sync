# Contributing

## Source of Truth

- Primary CLI implementation: `src/sync_onelap_strava/cli.py`
- Compatibility wrapper only: `run_sync.py`
- Runtime logic stays in `src/sync_onelap_strava/*`
- Skill distribution is maintained in standalone repo `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills`

## Local Development

1. Install dependencies:
   - `pip install -r requirements-dev.txt`
2. Install package in editable mode:
   - `python -m pip install -e .`
3. Run tests:
   - `python -m pytest -q`

## Global CLI Contract

- Console command: `onelap-sync`
- Defined in `pyproject.toml`:
  - `[project.scripts] onelap-sync = "sync_onelap_strava.cli:main"`
- If command is not found on Windows after local install, add this to `PATH`:
  - `C:\Users\<you>\AppData\Roaming\Python\Python<version>\Scripts`

## When You Change CLI Flags or Behavior

Update all of the following together to avoid drift:

- `src/sync_onelap_strava/cli.py`
- `run_sync.py` (wrapper compatibility)
- `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/references/commands.md`
- `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/SKILL.md` (if trigger/usage changed)
- `README.md`
- `docs/skills-mapping.md`
- Tests under `tests/` (especially `tests/test_cli.py` and `tests/test_skill_repository_structure.py`)

## Skills Layout Rules

- Skill directory name in standalone repo uses English slug (`onelap-strava-sync`)
- Human-facing descriptions can be Chinese
- Runtime repo should not carry a local `skills/` directory anymore
