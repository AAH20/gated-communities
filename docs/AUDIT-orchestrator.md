# Independent Audit — gated-communities

**Auditor:** orchestrator subagent (adversarial verification pass)
**Date:** 2026-10-11
**Scope:** dependency, security, Python-version, test-integrity, dead/duplicate code.
Environment: repo venv `.venv/bin/python` = **Python 3.12.14**; system `python3` = **Python 3.9.6**.

---

## 1. Dependency audit

```text
$ ./.venv/bin/pip list --outdated 2>&1 | head -20
Package        Version Latest Type
filelock       3.32.7  4.1.0  wheel
pydantic       2.13.5  2.14.0 wheel
pydantic_core  2.46.5  2.50.0 wheel
safety-schemas 0.0.16  0.0.21 wheel
typer          0.25.1  0.27.3 wheel
uuid_utils     0.17.1  1.0.0  wheel
[exit=0]
```
**Outdated packages: 6.** (network confirmed live). `pydantic==2.13.5` / `pydantic-core==2.46.5` are **hard-pinned one minor behind** latest (2.14.0/2.50.0) with an in-file justification comment ("known-compatible pair").

Constraints: mostly unbounded `>=` (`fastapi>=0.115.0`, `sqlalchemy>=2.0.30` …) — no upper bounds. `requirements.txt` additionally piles up "security-pin" `>=` floors for transitive deps (`starlette>=1.3.1`, `click>=8.3.2`, `setuptools>=82.1.0`, `future>=1.0.0`, …). No `>=0.0` wildcards.

## 2. Security scan

`bandit` present in this venv (1.9.4).
```text
$ .venv/bin/python -m bandit -r src -ll 2>/dev/null | sed -n '/Run metrics/,$p'
Run metrics:
        Total issues (by severity):
                Low: 581
                Medium: 0
                High: 0
Files skipped (6):
        .../api/compliance_monitor___init__.py (syntax error while parsing AST from file)
        .../api/member_verification___init__.py (syntax error while parsing AST from file)
        .../api/reputation_system___init__.py (syntax error while parsing AST from file)
        .../compliance_monitor_main.py (syntax error while parsing AST from file)
        .../member_verification_main.py (syntax error while parsing AST from file)
        .../reputation_system_main.py (syntax error while parsing AST from file)
```
**MEDIUM+ findings: 0 — but 6 files were NOT SCANNED** because they do not parse. The zero is therefore **not trustworthy** for those files. See §3.

## 3. Python-version compatibility

- Declared: `requires-python = ">=3.10"`. CI matrix: `["3.10","3.11","3.12"]` — **correct**, tests the floor.
- **6 source files are syntactically invalid on ALL Python versions (verified on 3.12 too):**
```text
$ .venv/bin/python -c "compile(open(f).read(),f,'exec')"
api/compliance_monitor___init__.py:3: from ..api. audits, policies, remediation, scores, violations
                                                    ^ SyntaxError: invalid syntax
api/member_verification___init__.py:3: from ..api. agents, documents, fraud, health, trust, verification
api/reputation_system___init__.py:4:   from ..api. (
compliance_monitor_main.py:9:          from ..api. audits, policies, remediation, scores, violations
member_verification_main.py:10:        from ..api. agents, documents, fraud, health, trust, verification
reputation_system_main.py:10:          from ..api. api_router
```
This is **not** a Python-version mismatch — the mangled `from ..api. <name>, <name>` form is invalid grammar everywhere. It is the fingerprint of a broken regex import-rewriter: the repo ships `fix_imports.py` (12 KB) and `fix_imports2.py` (8 KB) in its root. bandit, mypy and pytest all silently skip these files.

**Verdict: version declaration is fine; 6 committed source files are broken.**

## 4. Test-suite integrity

```text
$ .venv/bin/python -m pytest tests -q --no-header --tb=line
==== 190 failed, 357 passed, 18 skipped, 815 warnings, 109 errors in 47.86s ====
```
**REAL tail line: `190 failed, 357 passed, 18 skipped, 109 errors`.**

A second full run produced a **different** result — the suite is **non-deterministic / flaky**:
```
first run : 227 failed, 318 passed, 18 skipped, 115 errors
second run: 190 failed, 357 passed, 18 skipped, 109 errors
```
Top error reasons (from `--tb=line`):
```
 59  E   assert 404 == 200                      # routes not mounted where expected
 28  E   AssertionError: {"detail":"Not Found"}
 26  E   NotImplementedError: Wire this fixture to the real FastAPI app instance.
 22  E   assert 404 == 422
 15  E   NameError: name 'CommunityManager' is not defined
  7  E   TypeError: 'email' is an invalid keyword argument for Member
  5  E   TypeError: PostService.__init__() got an unexpected keyword argument 'db'
  5  E   AttributeError: 'ModerationService' object has no attribute 'create_item'
  3  E   AttributeError: 'ModerationQueue' object has no attribute 'enqueue'
```
These are **test/impl API drift** (tests call `PostService(db=…)`, `check_access(db=…)`, `Member(email=…)` — signatures the implementation rejects) plus 26 explicit `NotImplementedError` stub fixtures. `.github/workflows/ci.yml:134` runs pytest with a trailing **`|| true`**, so a red suite never fails CI.

### Quarantined / deleted tests

- **`tests/_drift/`** — 22 files (~700 KB) moved out of `tests/` by commit `84e917f` ("quarantine drift tests"), and `pytest.ini` adds `--ignore=tests/_drift`. **Every import target of these files EXISTS** (`gated_communities.access_control`, `services.access_service`, `services.community_service`, `agents.moderation_queue`, …). Forcing them to run:
```text
$ .venv/bin/python -m pytest tests/_drift -q --no-header
979 failed, 30 passed, 141 warnings, 226 errors in 39.36s
```
  i.e. **~1,235 test cases** of intended coverage were removed from the run; they fail not because modules are missing but because the **tests drifted from the implementation** (`CommunityConfig.__init__() got an unexpected keyword argument 'name'`, `check_access() got an unexpected keyword argument 'db'`). This represents large, silently-orphaned coverage — and there is **no `_drift/README.md`** recording it (only `_unimplemented/` has one).
- **`tests/_unimplemented/`** — 7 "phantom" files whose imports (`src.websocket.connection`, `src.access_control`, `src.reputation`, `TierManager`) never existed; `pytest.ini`/`pyproject.toml` ignore the dir. Documented by `tests/_unimplemented/README.md`. Legitimate quarantine.

## 5. Dead / duplicate code signal

- **57 git-tracked `*___init__.py` triple-underscore files** (`git ls-files 'src/**/*___init__.py' | wc -l` → 57), e.g. `api/compliance_monitor___init__.py`, `config/member_verification___init__.py`, `models/reputation_system___init__.py`. These are artifacts of a botched rename of `__init__.py` and have no legitimate Python meaning.
- **30 service modules fail to import** at load time due to a literal `{{}}` initializer:
```text
$ ../.venv/bin/python -c "import gated_communities.services.badge_service"
services/badge_service.py:27: self._items: dict[str, dict[str, Any]] = {{}}
                                                                        ^^^^
TypeError: unhashable type: 'dict'
```
  (`{{}}` builds a **set containing a dict**.) Affected (30): agent, badge, benefit, bulk, dispute, document, escalation, export, fraud, health, import, item, policy, priority, queue, report, reputation, resolution, review, rule, score, search, settings, sla, tier, trust, upgrade, verification, violation, webhook services — instantiated at module import (e.g. `badge_service.py:147 _default_service = BadgeServiceService()`).
- Full import scan: **63 modules fail to import** — 6 SyntaxError, ~24 broken absolute imports (`No module named 'moderation_queue'`, `'escalation_workflow'`, `'community_health_scorer'`, `'gated_communities.agents.models'`, …), 30 `{{}}` `TypeError`s, and a handful of missing optional deps (`redis`, `langchain_openai`, `celery`).

---

## Top 3 REAL issues (ranked)

1. **[VERIFIED DEFECT — CRITICAL] 30 service modules unimportable + 6 files with hard SyntaxErrors.** `{{}}`-initializer bug (`TypeError: unhashable type: 'dict'` at import) plus mangled `from ..api. …` imports. The package's own modules cannot be imported; bandit/mypy silently skip the 6 broken files.
2. **[VERIFIED DEFECT — HIGH] The live test suite is substantially red AND flaky, and CI hides it.** Real result `190 failed, 357 passed, 18 skipped, 109 errors` (a second run: `227/318/115`). CI appends `|| true`, so this never blocks merges.
3. **[VERIFIED DEFECT — HIGH] Quarantine hides real coverage.** `tests/_drift` (22 files, ~1,235 cases) was excluded from collection although **every module it imports exists**; running it yields `979 failed / 30 passed / 226 errors` from API drift, and the quarantine is undocumented. 57 duplicate `*___init__.py` files are also dead weight.

### Minimal, verifiable fix (one per repo) — `docs/AUDIT-orchestrator.patch`
Mechanically replaces `= {{}}` → `= {}` across the **30** affected service modules (one conceptual fix, verified to apply):
```text
$ git -C gated-communities apply --check docs/AUDIT-orchestrator.patch
[exit=0]
```
> This is a **patch artifact only** — no `src/**`, `tests/**`, or `.github/**` file was modified by this audit (out of scope). A source-owning agent should apply it, then repeat the `{{}}`→`{}` fix for any non-`= {{}}` variants, and delete the 57 `*___init__.py` artifacts.
