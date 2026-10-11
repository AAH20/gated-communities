# Dead / Unimportable Modules

Package-wide import scan of `gated_communities` (349 modules) run with:

```bash
PYTHONPATH=src .venv/bin/python - <<'PY'
import importlib, pathlib
pkg = importlib.import_module("gated_communities")
root = pathlib.Path(pkg.__path__[0])
names = []
for p in sorted(root.rglob("*.py")):
    parts = list(p.relative_to(root.parent).with_suffix("").parts)
    if parts[-1] == "__init__": parts = parts[:-1]
    if not parts or "tests" in parts: continue
    names.append(".".join(parts))
ok = fail = 0; bad = []
for n in names:
    try:
        importlib.import_module(n); ok += 1
    except BaseException as e:
        fail += 1; bad.append(f"{n}: {type(e).__name__}: {str(e)[:90]}")
print(f"TOTAL {len(names)} | OK {ok} | FAIL {fail}")
[print(' ', b) for b in bad]
PY
```

Before: `TOTAL 349 | OK 305 | FAIL 44`
After:  `TOTAL 349 | OK 348 | FAIL 1`

All 43 repairable modules were fixed by pointing them at the real in-repo
targets. The single remaining module below cannot be repaired by changing an
import path because it references a **symbol that does not exist anywhere in
the repository**. Per policy it is **not deleted**; it is recorded here.

---

## 1. `src/gated_communities/community_governance_main.py`

**Status:** DEAD — unimportable, and no module or test references it.

**Reproducer:**

```bash
$ PYTHONPATH=src .venv/bin/python -c "import gated_communities.community_governance_main"
ModuleNotFoundError: No module named 'community_governance'
```

**Unresolvable import line (line 20):**

```python
from community_governance.exceptions import GovernanceException
```

There is no top-level `community_governance` package, and the vendored
exception module (`gated_communities/community_governance_exceptions.py`)
defines the base class as **`GovernanceError`**, not `GovernanceException`:

```bash
$ grep -rn "class GovernanceException" src/
# (no output — the symbol does not exist anywhere)

$ grep -rn "GovernanceException" src/ tests/ --include=*.py
src/gated_communities/community_governance_main.py:20:from community_governance.exceptions import GovernanceException
src/gated_communities/community_governance_main.py:158:    @app.exception_handler(GovernanceException)
src/gated_communities/community_governance_main.py:160:        request: Request, exc: GovernanceException

$ grep -rn "class GovernanceError" src/gated_communities/community_governance_exceptions.py
src/gated_communities/community_governance_exceptions.py:8:class GovernanceError(Exception):
```

The symbol is referenced **only by the dead module itself** (self-references
only) — it is a renamed artifact, not a path that can be redirected.

**Evidence that nothing references this module** (self-references only; the
file is not imported by any other module or test):

```bash
$ grep -rn "community_governance_main" src/ tests/ --include=*.py
# (no output; exit status 1)
```

**Note for the owner:** every *other* import in this file does have a real home
in the repo and could be redirected (`community_governance.api.dependencies` →
`gated_communities.api.community_governance_dependencies`;
`community_governance.config.logging_config` →
`gated_communities.config.community_governance_logging_config`;
`community_governance.config.settings` →
`gated_communities.config.community_governance_settings`;
`community_governance.integrations` →
`gated_communities.integrations.community_governance___init__`;
`community_governance.agents` → `gated_communities.agents.community_governance`).
It also imports a multi-submodule fan-out
(`from community_governance.api.routes import analytics, disputes, explain,
health, metrics, policies, rules`) that has no single flattened equivalent.
The module was left untouched because it cannot be made importable without
either inventing a `GovernanceException` alias or renaming the symbol — a
semantic change beyond an import-path repair, which requires the owner's
decision. Deletion likewise requires explicit owner approval.
