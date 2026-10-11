"""Guard: every module in ``gated_communities.services`` must be importable.

30 service modules were generated with a templating artifact::

    self._items: dict[str, dict[str, Any]] = {{}}

``{{}}`` is a *set containing a dict*, which raises
``TypeError: unhashable type: 'dict'`` at class-body execution — i.e. at
**import time**. Each of those modules was therefore unimportable.

No test imported them, so nothing caught it. This test imports every submodule
of the package and fails with the full list of offenders, so a single broken
module can never hide behind a green suite again.
"""

from __future__ import annotations

import importlib
import pkgutil


def test_every_service_module_imports():
    """Import all submodules of gated_communities.services; report any failure."""
    package = importlib.import_module("gated_communities.services")

    failures: list[str] = []
    for module_info in pkgutil.iter_modules(package.__path__):
        name = f"{package.__name__}.{module_info.name}"
        try:
            importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 - we want every failure class
            failures.append(f"{name}: {type(exc).__name__}: {exc}")

    assert not failures, "unimportable service modules:\n" + "\n".join(failures)
