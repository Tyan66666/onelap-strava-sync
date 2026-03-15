# Sync OneLap Strava Agent Skills Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a standalone `sync_onelap_strava_agent_skills` repository whose `onelap-strava-sync` skill works immediately after copy to `~/.agents/skills/`, with first-trigger isolated venv bootstrap.

**Architecture:** Create a dedicated distribution repository containing one self-contained skill. Keep all runtime Python modules inside `onelap-strava-sync/scripts/`, route all executions through `scripts/bootstrap.py`, and manage dependencies in a skill-specific venv at `~/.agents/venvs/onelap-strava-sync/`. Maintain code parity with the runtime project via a sync script plus smoke tests.

**Tech Stack:** Python 3, venv, pip, PowerShell, pytest, Agent Skills (`SKILL.md`) format.

---

### Task 1: Create standalone repository skeleton

**Files:**
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/README.md`
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/.gitignore`
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/SKILL.md`
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/references/commands.md`
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/__init__.py`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_skill_scaffold_exists():
    root = Path(r"C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills")
    assert (root / "onelap-strava-sync" / "SKILL.md").is_file()
    assert (root / "onelap-strava-sync" / "references" / "commands.md").is_file()
    assert (root / "onelap-strava-sync" / "scripts" / "__init__.py").is_file()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_scaffold.py::test_skill_scaffold_exists -v`
Expected: FAIL with missing files

**Step 3: Write minimal implementation**

Create directory tree and minimal file placeholders.

`SKILL.md` minimal frontmatter:

```md
---
name: onelap-strava-sync
description: Sync OneLap FIT activities to Strava with first-run bootstrap. Use when user asks to run OneLap/Strava sync or auth init flows.
compatibility: Requires Python 3 and internet access for first dependency install.
---
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_scaffold.py::test_skill_scaffold_exists -v`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md .gitignore onelap-strava-sync/SKILL.md onelap-strava-sync/references/commands.md onelap-strava-sync/scripts/__init__.py tests/test_scaffold.py
git commit -m "chore: scaffold standalone onelap skill repository"
```

### Task 2: Port runtime modules into skill scripts

**Files:**
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/sync_onelap_strava/__init__.py`
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/sync_onelap_strava/config.py`
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/sync_onelap_strava/onelap_auth_init.py`
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/sync_onelap_strava/onelap_client.py`
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/sync_onelap_strava/strava_client.py`
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/sync_onelap_strava/strava_oauth_init.py`
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/sync_onelap_strava/sync_engine.py`
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/sync_onelap_strava/state_store.py`
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/sync_onelap_strava/logging_setup.py`
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/sync_onelap_strava/env_store.py`
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/sync_onelap_strava/dedupe_service.py`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_ported_runtime_modules_exist():
    root = Path(r"C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/sync_onelap_strava")
    required = [
        "__init__.py",
        "config.py",
        "onelap_auth_init.py",
        "onelap_client.py",
        "strava_client.py",
        "strava_oauth_init.py",
        "sync_engine.py",
        "state_store.py",
        "logging_setup.py",
        "env_store.py",
        "dedupe_service.py",
    ]
    for name in required:
        assert (root / name).is_file(), name
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ported_modules.py::test_ported_runtime_modules_exist -v`
Expected: FAIL with missing module files

**Step 3: Write minimal implementation**

Copy current project runtime modules from `src/sync_onelap_strava/` into `onelap-strava-sync/scripts/sync_onelap_strava/` without behavioral changes.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_ported_modules.py::test_ported_runtime_modules_exist -v`
Expected: PASS

**Step 5: Commit**

```bash
git add onelap-strava-sync/scripts/sync_onelap_strava tests/test_ported_modules.py
git commit -m "feat: port runtime sync modules into skill scripts"
```

### Task 3: Add skill-local runner entrypoint

**Files:**
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/run_sync.py`
- Test: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/tests/test_run_sync_entrypoint.py`

**Step 1: Write the failing test**

```python
import runpy
from pathlib import Path


def test_run_sync_entrypoint_exists_and_executes_module_import_path():
    target = Path(r"C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/run_sync.py")
    assert target.is_file()
    runpy.run_path(str(target), run_name="__main__")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_run_sync_entrypoint.py::test_run_sync_entrypoint_exists_and_executes_module_import_path -v`
Expected: FAIL because `run_sync.py` missing or import error

**Step 3: Write minimal implementation**

```python
from sync_onelap_strava.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_run_sync_entrypoint.py::test_run_sync_entrypoint_exists_and_executes_module_import_path -v`
Expected: PASS

**Step 5: Commit**

```bash
git add onelap-strava-sync/scripts/run_sync.py tests/test_run_sync_entrypoint.py
git commit -m "feat: add skill-local sync entrypoint"
```

### Task 4: Implement lazy bootstrap with isolated venv

**Files:**
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/bootstrap.py`
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/requirements.txt`
- Test: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/tests/test_bootstrap.py`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_bootstrap_declares_isolated_venv_target():
    file = Path(r"C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts/bootstrap.py")
    text = file.read_text(encoding="utf-8") if file.exists() else ""
    assert "~/.agents/venvs/onelap-strava-sync" in text or ".agents/venvs/onelap-strava-sync" in text
```
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_bootstrap.py::test_bootstrap_declares_isolated_venv_target -v`
Expected: FAIL because bootstrap file missing or no venv path

**Step 3: Write minimal implementation**

Implement bootstrap responsibilities:

- Resolve venv dir: `Path.home() / ".agents" / "venvs" / "onelap-strava-sync"`
- Create venv if missing
- Install `requirements.txt` with venv pip
- Save fingerprint file (python version + requirements hash)
- Reinstall when fingerprint mismatch
- Execute `run_sync.py` via venv python, forwarding CLI args

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_bootstrap.py::test_bootstrap_declares_isolated_venv_target -v`
Expected: PASS

**Step 5: Commit**

```bash
git add onelap-strava-sync/scripts/bootstrap.py onelap-strava-sync/scripts/requirements.txt tests/test_bootstrap.py
git commit -m "feat: add lazy bootstrap with isolated skill venv"
```

### Task 5: Wire SKILL commands through bootstrap

**Files:**
- Modify: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/SKILL.md`
- Modify: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/references/commands.md`
- Test: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/tests/test_skill_commands.py`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_skill_commands_route_to_bootstrap():
    skill_md = Path(r"C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/SKILL.md").read_text(encoding="utf-8")
    assert "scripts/bootstrap.py" in skill_md
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_skill_commands.py::test_skill_commands_route_to_bootstrap -v`
Expected: FAIL if SKILL still points to direct python runner

**Step 3: Write minimal implementation**

Update skill instructions so all execution examples use bootstrap, e.g.:

`python scripts/bootstrap.py --since 2026-03-01`

Include modes:

- `--onelap-auth-init`
- `--strava-auth-init`
- `--since YYYY-MM-DD`
- `--download-only`

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_skill_commands.py::test_skill_commands_route_to_bootstrap -v`
Expected: PASS

**Step 5: Commit**

```bash
git add onelap-strava-sync/SKILL.md onelap-strava-sync/references/commands.md tests/test_skill_commands.py
git commit -m "docs: route skill commands through bootstrap launcher"
```

### Task 6: Add sync helper from runtime repo

**Files:**
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/tools/sync_from_runtime.ps1`
- Test: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/tests/test_sync_script.py`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_sync_script_exists_and_mentions_source_target_paths():
    path = Path(r"C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/tools/sync_from_runtime.ps1")
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    assert "src/sync_onelap_strava" in text
    assert "onelap-strava-sync/scripts/sync_onelap_strava" in text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_sync_script.py::test_sync_script_exists_and_mentions_source_target_paths -v`
Expected: FAIL until sync script exists

**Step 3: Write minimal implementation**

Implement PowerShell sync script with parameters:

- `-RuntimeRepoPath`
- `-SkillRepoPath`

Operations:

- Copy `src/sync_onelap_strava/*.py`
- Copy `run_sync.py`
- Optionally copy/refresh dependency list
- Exit non-zero on copy failure

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_sync_script.py::test_sync_script_exists_and_mentions_source_target_paths -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tools/sync_from_runtime.ps1 tests/test_sync_script.py
git commit -m "chore: add runtime-to-skill sync helper"
```

### Task 7: Add end-to-end bootstrap smoke test

**Files:**
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/tests/test_bootstrap_smoke.py`

**Step 1: Write the failing test**

```python
import subprocess
from pathlib import Path


def test_bootstrap_help_command_runs():
    root = Path(r"C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/scripts")
    cmd = ["python", "bootstrap.py", "--help"]
    result = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    assert result.returncode == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_bootstrap_smoke.py::test_bootstrap_help_command_runs -v`
Expected: FAIL before bootstrap wiring is complete

**Step 3: Write minimal implementation**

Finalize bootstrap argument forwarding and ensure `--help` path does not require live credentials.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_bootstrap_smoke.py::test_bootstrap_help_command_runs -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_bootstrap_smoke.py
git commit -m "test: add bootstrap smoke execution check"
```

### Task 8: Document usage and handoff workflow

**Files:**
- Modify: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/README.md`
- Modify: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/onelap-strava-sync/references/commands.md`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_readme_documents_copy_and_first_trigger_bootstrap():
    text = Path(r"C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/README.md").read_text(encoding="utf-8")
    assert "~/.agents/skills/" in text
    assert "first trigger" in text.lower()
    assert "isolated venv" in text.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_docs.py::test_readme_documents_copy_and_first_trigger_bootstrap -v`
Expected: FAIL until README is complete

**Step 3: Write minimal implementation**

Document:

- copy path (`~/.agents/skills/`)
- first-trigger bootstrap behavior
- venv location
- troubleshooting for missing network/python

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_docs.py::test_readme_documents_copy_and_first_trigger_bootstrap -v`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md onelap-strava-sync/references/commands.md tests/test_docs.py
git commit -m "docs: add copy-and-run workflow for standalone skill"
```

### Task 9: Full validation before release

**Files:**
- Modify: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/.github/workflows/ci.yml` (if CI exists)
- Create: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/.github/workflows/ci.yml` (if CI absent)

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_ci_runs_pytest():
    wf = Path(r"C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/.github/workflows/ci.yml")
    text = wf.read_text(encoding="utf-8") if wf.exists() else ""
    assert "pytest" in text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ci.py::test_ci_runs_pytest -v`
Expected: FAIL until CI file exists

**Step 3: Write minimal implementation**

Create CI workflow that runs:

- `python -m pip install -r dev requirements`
- `pytest -q`

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_ci.py::test_ci_runs_pytest -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .github/workflows/ci.yml tests/test_ci.py
git commit -m "ci: add pytest validation for skill distribution repo"
```

### Task 10: Manual acceptance validation in agent environment

**Files:**
- Modify: `C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/README.md`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_acceptance_checklist_present():
    readme = Path(r"C:/Users/13247/Documents/Code Project/sync_onelap_strava_agent_skills/README.md").read_text(encoding="utf-8")
    assert "Acceptance checklist" in readme
    assert "--onelap-auth-init" in readme
    assert "--strava-auth-init" in readme
    assert "--download-only" in readme
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_acceptance_docs.py::test_acceptance_checklist_present -v`
Expected: FAIL until checklist is added

**Step 3: Write minimal implementation**

Add acceptance checklist commands:

1. Copy `onelap-strava-sync` into `~/.agents/skills/`
2. Trigger skill with auth init command
3. Verify venv appears under `~/.agents/venvs/onelap-strava-sync/`
4. Verify command modes run successfully

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_acceptance_docs.py::test_acceptance_checklist_present -v`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md tests/test_acceptance_docs.py
git commit -m "docs: add acceptance checklist for copy-and-run skill usage"
```
