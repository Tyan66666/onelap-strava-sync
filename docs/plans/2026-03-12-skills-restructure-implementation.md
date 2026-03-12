# Skills Repository Restructure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a dual-track `skills/` distribution layer that global agent config can reference directly, while keeping the current Python project as source of truth and preserving runtime behavior.

**Architecture:** Keep all executable logic in `run_sync.py` and `src/sync_onelap_strava/*`. Add a non-invasive skill shell under `skills/onelap-strava-sync/` plus mapping docs. Enforce the structure and content with focused pytest contract tests.

**Tech Stack:** Python 3.11, pytest, Markdown docs, existing CLI entrypoint (`run_sync.py`)

---

### Task 1: Define structure contract tests

**Files:**
- Create: `tests/test_skill_repository_structure.py`
- Test: `tests/test_skill_repository_structure.py`

**Step 1: Write the failing test**

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_skill_distribution_files_exist():
    skill_root = ROOT / "skills" / "onelap-strava-sync"
    assert skill_root.is_dir()
    assert (skill_root / "SKILL.md").is_file()
    assert (skill_root / "resources").is_dir()
    assert (skill_root / "resources" / "commands.md").is_file()
```

**Step 2: Run test to verify it fails**

Run: `rtk test "pytest tests/test_skill_repository_structure.py::test_skill_distribution_files_exist -v"`
Expected: FAIL because `skills/onelap-strava-sync/` does not exist yet.

**Step 3: Commit the failing test first (TDD checkpoint)**

```bash
rtk git add tests/test_skill_repository_structure.py && rtk git commit -m "test: define skills distribution structure contract"
```

**Step 4: Confirm commit and working tree**

Run: `rtk git status --short`
Expected: clean tree or only unrelated pre-existing changes.

**Step 5: Move to implementation task**

No code changes in this task beyond test creation.

### Task 2: Create minimal skills shell to satisfy structure contract

**Files:**
- Create: `skills/onelap-strava-sync/SKILL.md`
- Create: `skills/onelap-strava-sync/resources/commands.md`
- Test: `tests/test_skill_repository_structure.py`

**Step 1: Write minimal implementation**

```markdown
# OneLap to Strava Sync Skill

This skill wraps the existing root CLI without moving source code.
```

```markdown
# Commands

- `python run_sync.py`
```

**Step 2: Run test to verify it passes**

Run: `rtk test "pytest tests/test_skill_repository_structure.py::test_skill_distribution_files_exist -v"`
Expected: PASS.

**Step 3: Run a quick formatting/lint sanity check (optional)**

Run: `rtk test "pytest tests/test_import_smoke.py -q"`
Expected: PASS.

**Step 4: Commit**

```bash
rtk git add skills/onelap-strava-sync/SKILL.md skills/onelap-strava-sync/resources/commands.md && rtk git commit -m "docs: add minimal skills distribution shell"
```

**Step 5: Verify status**

Run: `rtk git status --short`
Expected: clean tree or unrelated pre-existing changes only.

### Task 3: Add content-policy tests (naming, commands, mapping doc)

**Files:**
- Modify: `tests/test_skill_repository_structure.py`
- Test: `tests/test_skill_repository_structure.py`

**Step 1: Write the failing tests**

```python
def test_skill_uses_english_slug_and_chinese_display_name():
    skill_root = ROOT / "skills" / "onelap-strava-sync"
    assert skill_root.name == "onelap-strava-sync"
    assert skill_root.name.isascii()
    text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    assert "中文名" in text


def test_skill_commands_cover_primary_cli_modes():
    text = (ROOT / "skills" / "onelap-strava-sync" / "resources" / "commands.md").read_text(
        encoding="utf-8"
    )
    assert "python run_sync.py" in text
    assert "--since" in text
    assert "--download-only" in text
    assert "--strava-auth-init" in text


def test_skills_mapping_doc_links_to_root_entrypoints():
    mapping = (ROOT / "docs" / "skills-mapping.md").read_text(encoding="utf-8")
    assert "run_sync.py" in mapping
    assert "src/sync_onelap_strava" in mapping
```

**Step 2: Run tests to verify failure**

Run: `rtk test "pytest tests/test_skill_repository_structure.py -v"`
Expected: FAIL (missing mapping doc and missing required content keywords).

**Step 3: Commit the failing tests**

```bash
rtk git add tests/test_skill_repository_structure.py && rtk git commit -m "test: enforce skill naming and mapping content contracts"
```

**Step 4: Verify status**

Run: `rtk git status --short`
Expected: clean tree or unrelated pre-existing changes only.

**Step 5: Move to implementation task**

No additional implementation in this task.

### Task 4: Implement full skill docs and mapping docs

**Files:**
- Modify: `skills/onelap-strava-sync/SKILL.md`
- Modify: `skills/onelap-strava-sync/resources/commands.md`
- Create: `skills/onelap-strava-sync/README.md`
- Create: `docs/skills-mapping.md`
- Test: `tests/test_skill_repository_structure.py`

**Step 1: Write minimal implementation that satisfies tests**

```markdown
# OneLap to Strava Sync

中文名：OneLap 同步 Strava

## Purpose

Use this skill to run OneLap -> Strava sync workflows through the existing root CLI.

## Trigger

- User asks to sync OneLap FIT files to Strava
- User asks for download-only exports
- User asks to initialize Strava OAuth tokens

## Usage

See `resources/commands.md` for exact commands.
```

```markdown
# Command Reference

- Default sync: `python run_sync.py`
- Since date: `python run_sync.py --since 2026-03-01`
- Download only: `python run_sync.py --download-only --since 2026-03-01`
- Strava OAuth init: `python run_sync.py --strava-auth-init`
```

```markdown
# Skills to Root Code Mapping

## Skill

- `skills/onelap-strava-sync/SKILL.md`

## Entrypoint

- `run_sync.py`

## Runtime modules

- `src/sync_onelap_strava/config.py`
- `src/sync_onelap_strava/onelap_client.py`
- `src/sync_onelap_strava/strava_client.py`
- `src/sync_onelap_strava/sync_engine.py`

## Maintenance rule

- Business logic changes happen in root source files, not in `skills/`.
```

**Step 2: Run tests to verify pass**

Run: `rtk test "pytest tests/test_skill_repository_structure.py -v"`
Expected: PASS.

**Step 3: Run a targeted CLI regression check**

Run: `rtk test "pytest tests/test_cli.py::test_run_sync_script_help_exits_zero tests/test_cli_download_only.py::test_download_only_mode_does_not_require_strava_settings -v"`
Expected: PASS.

**Step 4: Commit**

```bash
rtk git add skills/onelap-strava-sync/SKILL.md skills/onelap-strava-sync/README.md skills/onelap-strava-sync/resources/commands.md docs/skills-mapping.md && rtk git commit -m "docs: add skill docs and root mapping for dual-track layout"
```

**Step 5: Verify status**

Run: `rtk git status --short`
Expected: clean tree or unrelated pre-existing changes only.

### Task 5: Add discoverability guardrail in root README

**Files:**
- Modify: `tests/test_skill_repository_structure.py`
- Modify: `README.md`
- Test: `tests/test_skill_repository_structure.py`

**Step 1: Write the failing test**

```python
def test_root_readme_references_skills_mapping_doc():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/skills-mapping.md" in readme
```

**Step 2: Run test to verify failure**

Run: `rtk test "pytest tests/test_skill_repository_structure.py::test_root_readme_references_skills_mapping_doc -v"`
Expected: FAIL until README includes the mapping doc path.

**Step 3: Implement minimal README update**

```markdown
## Skills Distribution

This repository keeps runtime code in root source directories and exposes a distribution-friendly skill at `skills/onelap-strava-sync/`.

Mapping between skill artifacts and runtime entrypoints: `docs/skills-mapping.md`.
```

**Step 4: Run tests to verify pass**

Run: `rtk test "pytest tests/test_skill_repository_structure.py -v"`
Expected: PASS.

**Step 5: Commit**

```bash
rtk git add README.md tests/test_skill_repository_structure.py && rtk git commit -m "docs: document skills mapping entrypoint in root readme"
```

### Task 6: Final regression and completion

**Files:**
- Test: `tests/test_skill_repository_structure.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_cli_download_only.py`
- Test: `tests/test_import_smoke.py`

**Step 1: Run focused regression suite**

Run: `rtk test "pytest tests/test_skill_repository_structure.py tests/test_cli.py tests/test_cli_download_only.py tests/test_import_smoke.py -q"`
Expected: all PASS.

**Step 2: Run compact git diff review**

Run: `rtk git diff --staged && rtk git diff`
Expected: only docs/skills layer and tests/readme updates related to this plan.

**Step 3: Final integration commit (if any uncommitted changes remain)**

```bash
rtk git add docs/skills-mapping.md skills/onelap-strava-sync README.md tests/test_skill_repository_structure.py && rtk git commit -m "feat: finalize dual-track skills repository layout"
```

**Step 4: Verify clean status**

Run: `rtk git status --short`
Expected: clean tree or unrelated pre-existing changes only.

**Step 5: Capture evidence for handoff**

Record test command outputs and the list of newly created skill files in the final implementation summary.
