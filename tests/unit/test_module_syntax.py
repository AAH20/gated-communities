"""Guard: every Python file in the package must at least parse.

Six generated modules contained a malformed import that is a hard
``SyntaxError``::

    from ..api. audits, policies, remediation, scores, violations

``from ..api. <space> names`` is not valid Python; the intended form is
``from ..api import audits, policies, ...``. Because a SyntaxError only fires
when the file is imported, and nothing imported them, the breakage sat
undetected. Files affected:

* ``member_verification_main.py``
* ``reputation_system_main.py``
* ``compliance_monitor_main.py``
* ``api/compliance_monitor___init__.py``
* ``api/member_verification___init__.py``
* ``api/reputation_system___init__.py``

This test parses every module in the package so a syntax break anywhere fails
CI immediately instead of waiting for someone to import the file.

Note: this asserts *parseability* only. Some modules still fail at import time
for unrelated reasons (missing optional deps, unresolved submodule paths);
those are tracked separately and are deliberately not masked here.
"""

from __future__ import annotations

import ast
import pathlib

import gated_communities

_PACKAGE_ROOT = pathlib.Path(gated_communities.__path__[0])


def _python_files() -> list[pathlib.Path]:
    return sorted(p for p in _PACKAGE_ROOT.rglob("*.py"))


def test_package_contains_python_files():
    """Sanity: the scan actually finds files (guards against a bad root)."""
    assert _python_files(), f"no .py files found under {_PACKAGE_ROOT}"


def test_every_module_parses():
    """Every module in the package must be syntactically valid."""
    failures: list[str] = []
    for path in _python_files():
        try:
            ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError as exc:
            rel = path.relative_to(_PACKAGE_ROOT.parent)
            failures.append(f"{rel}:{exc.lineno}: {exc.msg}")

    assert not failures, "modules with syntax errors:\n" + "\n".join(failures)
