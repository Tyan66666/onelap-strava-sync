# Strava Auth Init Automation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a one-time Strava OAuth initialization command that writes tokens to `.env`, then keep tokens updated automatically on refresh so daily sync runs unattended.

**Architecture:** Add a dedicated OAuth init module for URL generation, localhost callback handling, code exchange, and `.env` persistence. Keep runtime sync flow intact while extending token refresh to persist updated credentials. Wire both through `run_sync.py` with a new `--strava-auth-init` mode.

**Tech Stack:** Python 3.14, `requests`, stdlib `http.server`, stdlib `webbrowser`, `pytest`, `responses`

---

### Task 1: Add `.env` Token Persistence Helper

**Files:**
- Create: `src/sync_onelap_strava/env_store.py`
- Test: `tests/test_env_store.py`

**Step 1: Write the failing test**

Create `tests/test_env_store.py` with:

```python
from pathlib import Path

from sync_onelap_strava.env_store import upsert_env_values


def test_upsert_env_values_updates_existing_and_appends_missing(tmp_path):
    env_path = Path(tmp_path) / ".env"
    env_path.write_text(
        "\n".join(
            [
                "STRAVA_CLIENT_ID=210500",
                "STRAVA_ACCESS_TOKEN=old-access",
                "ONELAP_USERNAME=user1",
            ]
        ),
        encoding="utf-8",
    )

    upsert_env_values(
        env_path,
        {
            "STRAVA_ACCESS_TOKEN": "new-access",
            "STRAVA_REFRESH_TOKEN": "new-refresh",
            "STRAVA_EXPIRES_AT": "1773255475",
        },
    )

    content = env_path.read_text(encoding="utf-8")
    assert "STRAVA_ACCESS_TOKEN=new-access" in content
    assert "STRAVA_REFRESH_TOKEN=new-refresh" in content
    assert "STRAVA_EXPIRES_AT=1773255475" in content
    assert "ONELAP_USERNAME=user1" in content
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_env_store.py::test_upsert_env_values_updates_existing_and_appends_missing -v`

Expected: FAIL with import/module error because helper file does not exist yet.

**Step 3: Write minimal implementation**

Create `src/sync_onelap_strava/env_store.py`:

```python
from pathlib import Path


def upsert_env_values(env_path: Path, values: dict[str, str]) -> None:
    path = Path(env_path)
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    remaining = dict(values)
    updated_lines: list[str] = []

    for line in lines:
        if not line or line.lstrip().startswith("#") or "=" not in line:
            updated_lines.append(line)
            continue

        key, _ = line.split("=", 1)
        if key in remaining:
            updated_lines.append(f"{key}={remaining.pop(key)}")
        else:
            updated_lines.append(line)

    for key, value in remaining.items():
        updated_lines.append(f"{key}={value}")

    path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_env_store.py::test_upsert_env_values_updates_existing_and_appends_missing -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_env_store.py src/sync_onelap_strava/env_store.py
git commit -m "feat: add .env token upsert helper"
```

### Task 2: Add OAuth Init Module (URL + Scope + Token Exchange)

**Files:**
- Create: `src/sync_onelap_strava/strava_oauth_init.py`
- Test: `tests/test_strava_oauth.py`

**Step 1: Write the failing tests**

Add to `tests/test_strava_oauth.py`:

```python
import responses

from sync_onelap_strava.strava_oauth_init import build_authorize_url, exchange_code_for_tokens


def test_build_authorize_url_includes_force_and_activity_write():
    url = build_authorize_url(client_id="210500", redirect_uri="http://localhost:8765/callback")
    assert "approval_prompt=force" in url
    assert "scope=read%2Cactivity%3Awrite" in url
    assert "client_id=210500" in url


@responses.activate
def test_exchange_code_for_tokens_returns_required_fields():
    responses.add(
        responses.POST,
        "https://www.strava.com/oauth/token",
        json={
            "access_token": "a1",
            "refresh_token": "r1",
            "expires_at": 1773255475,
        },
        status=200,
    )

    payload = exchange_code_for_tokens(
        client_id="210500",
        client_secret="secret",
        code="abc",
    )

    assert payload["access_token"] == "a1"
    assert payload["refresh_token"] == "r1"
    assert payload["expires_at"] == 1773255475
```

**Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_strava_oauth.py::test_build_authorize_url_includes_force_and_activity_write -v
python -m pytest tests/test_strava_oauth.py::test_exchange_code_for_tokens_returns_required_fields -v
```

Expected: FAIL (module/functions missing).

**Step 3: Write minimal implementation**

Create `src/sync_onelap_strava/strava_oauth_init.py`:

```python
from urllib.parse import urlencode

import requests


def build_authorize_url(client_id: str, redirect_uri: str) -> str:
    query = urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "approval_prompt": "force",
            "scope": "read,activity:write",
        }
    )
    return f"https://www.strava.com/oauth/authorize?{query}"


def exchange_code_for_tokens(client_id: str, client_secret: str, code: str) -> dict:
    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return {
        "access_token": payload["access_token"],
        "refresh_token": payload["refresh_token"],
        "expires_at": payload["expires_at"],
    }
```

**Step 4: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/test_strava_oauth.py::test_build_authorize_url_includes_force_and_activity_write -v
python -m pytest tests/test_strava_oauth.py::test_exchange_code_for_tokens_returns_required_fields -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_strava_oauth.py src/sync_onelap_strava/strava_oauth_init.py
git commit -m "feat: add Strava OAuth URL builder and code exchange"
```

### Task 3: Add Scope Validation + Local Callback Capture

**Files:**
- Modify: `src/sync_onelap_strava/strava_oauth_init.py`
- Test: `tests/test_strava_oauth.py`

**Step 1: Write the failing tests**

Add to `tests/test_strava_oauth.py`:

```python
import pytest

from sync_onelap_strava.strava_oauth_init import ensure_required_scope


def test_ensure_required_scope_accepts_activity_write():
    ensure_required_scope("read,activity:write")


def test_ensure_required_scope_raises_without_activity_write():
    with pytest.raises(ValueError):
        ensure_required_scope("read")
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_strava_oauth.py::test_ensure_required_scope_raises_without_activity_write -v`

Expected: FAIL (function missing).

**Step 3: Write minimal implementation**

Add to `src/sync_onelap_strava/strava_oauth_init.py`:

```python
def ensure_required_scope(scope_csv: str) -> None:
    scopes = {s.strip() for s in scope_csv.split(",") if s.strip()}
    if "activity:write" not in scopes:
        raise ValueError("missing required scope: activity:write")
```

Also add minimal callback helper for later CLI integration:

```python
from urllib.parse import parse_qs, urlparse


def parse_callback_url(url: str) -> tuple[str, str]:
    query = parse_qs(urlparse(url).query)
    code = (query.get("code") or [""])[0]
    scope = (query.get("scope") or [""])[0]
    if not code:
        raise ValueError("missing code in callback url")
    return code, scope
```

**Step 4: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/test_strava_oauth.py::test_ensure_required_scope_accepts_activity_write -v
python -m pytest tests/test_strava_oauth.py::test_ensure_required_scope_raises_without_activity_write -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_strava_oauth.py src/sync_onelap_strava/strava_oauth_init.py
git commit -m "feat: validate required Strava OAuth scopes"
```

### Task 4: Wire `--strava-auth-init` into CLI and Persist Tokens to `.env`

**Files:**
- Modify: `run_sync.py`
- Modify: `src/sync_onelap_strava/config.py` (if needed for env path helper)
- Modify: `src/sync_onelap_strava/strava_oauth_init.py`
- Test: `tests/test_cli.py`

**Step 1: Write the failing CLI test**

Add to `tests/test_cli.py`:

```python
def test_cli_runs_strava_auth_init_and_exits_zero(monkeypatch):
    monkeypatch.setenv("STRAVA_CLIENT_ID", "210500")
    monkeypatch.setenv("STRAVA_CLIENT_SECRET", "secret")

    called = {"ok": False}

    def fake_run_strava_auth_init(client_id, client_secret, env_file):
        assert client_id == "210500"
        assert client_secret == "secret"
        called["ok"] = True

    import run_sync

    monkeypatch.setattr(run_sync, "run_strava_auth_init", fake_run_strava_auth_init)

    code = run_sync.run_cli(["--strava-auth-init"])
    assert code == 0
    assert called["ok"]
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py::test_cli_runs_strava_auth_init_and_exits_zero -v`

Expected: FAIL (flag/function missing).

**Step 3: Write minimal implementation**

In `run_sync.py`:
- Add parser flag `--strava-auth-init`.
- Add `run_strava_auth_init(client_id, client_secret, env_file)` wrapper that:
  - validates non-empty credentials
  - invokes OAuth init flow (`strava_oauth_init` module)
  - writes tokens to `.env` via `upsert_env_values`
- In `run_cli`, branch early for auth-init mode and return 0/1.

Minimal flow (acceptable first cut):
- Prompt user to paste callback URL
- Parse URL + validate scope + exchange tokens + update `.env`

Note: Browser auto-open and localhost server can be added in Task 5 refinement to keep this step minimal and green.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cli.py::test_cli_runs_strava_auth_init_and_exits_zero -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_cli.py run_sync.py src/sync_onelap_strava/strava_oauth_init.py src/sync_onelap_strava/env_store.py
git commit -m "feat: add cli mode for Strava auth initialization"
```

### Task 5: Persist Token Refresh Back to `.env` During Runtime

**Files:**
- Modify: `src/sync_onelap_strava/strava_client.py`
- Test: `tests/test_strava_oauth.py`

**Step 1: Write the failing test**

Add to `tests/test_strava_oauth.py`:

```python
import os

import responses

from sync_onelap_strava.strava_client import StravaClient


@responses.activate
def test_refresh_token_persists_updated_values(monkeypatch):
    saved = {}

    def fake_save(_path, values):
        saved.update(values)

    monkeypatch.setattr("sync_onelap_strava.strava_client.upsert_env_values", fake_save)

    responses.add(
        responses.POST,
        "https://www.strava.com/oauth/token",
        json={
            "access_token": "new-token",
            "refresh_token": "new-refresh",
            "expires_at": 1773255475,
        },
        status=200,
    )

    client = StravaClient(
        client_id="id",
        client_secret="secret",
        refresh_token="old-refresh",
        access_token="expired",
        expires_at=0,
    )

    token = client.ensure_access_token()
    assert token == "new-token"
    assert saved["STRAVA_ACCESS_TOKEN"] == "new-token"
    assert saved["STRAVA_REFRESH_TOKEN"] == "new-refresh"
    assert saved["STRAVA_EXPIRES_AT"] == "1773255475"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_strava_oauth.py::test_refresh_token_persists_updated_values -v`

Expected: FAIL because no persistence call exists.

**Step 3: Write minimal implementation**

In `src/sync_onelap_strava/strava_client.py`:
- Import `Path`-based `.env` updater.
- After refresh success, call updater with current token values.
- Wrap persistence in `try/except` and keep returning token even on write failure.

Reference code:

```python
from sync_onelap_strava.env_store import upsert_env_values

# after updating self.access_token/self.refresh_token/self.expires_at
try:
    upsert_env_values(
        Path(".env"),
        {
            "STRAVA_ACCESS_TOKEN": self.access_token,
            "STRAVA_REFRESH_TOKEN": self.refresh_token,
            "STRAVA_EXPIRES_AT": str(self.expires_at),
        },
    )
except Exception:
    pass
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_strava_oauth.py::test_refresh_token_persists_updated_values -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_strava_oauth.py src/sync_onelap_strava/strava_client.py src/sync_onelap_strava/env_store.py
git commit -m "feat: persist refreshed Strava tokens to env"
```

### Task 6: Final Verification + Documentation Update

**Files:**
- Modify: `README.md`

**Step 1: Write the failing docs expectation**

Expectation: README includes one-time auth init command and states refresh is auto-persisted.

**Step 2: Run full relevant tests before docs edit**

Run:

```bash
python -m pytest tests/test_env_store.py tests/test_strava_oauth.py tests/test_cli.py tests/test_strava_upload.py tests/test_sync_engine.py -v
```

Expected: PASS.

**Step 3: Write minimal docs update**

Add to `README.md` setup/auth section:

```markdown
- One-time Strava auth init: `python run_sync.py --strava-auth-init`
- This flow requests `read,activity:write` and writes tokens to `.env`.
- During normal runs, refreshed Strava tokens are automatically persisted back to `.env`.
```

**Step 4: Run end-to-end verification command**

Run:

```bash
python run_sync.py --help
python run_sync.py --strava-auth-init
```

Expected:
- Help text includes `--strava-auth-init`.
- Auth init starts and guides OAuth flow.

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: describe one-time Strava auth init workflow"
```
