"""Regression tests for silent router-mount failures.

``register_all_routers()`` imports each router lazily and skips any that fail to
import or mount. That resilience is necessary (one unimplemented agent package
must not take down the whole API) but it silently hid a real outage: CI stayed
green while dozens of endpoints 404'd.

These tests pin down the two properties that make skipping safe to observe:

1. A known-good set of routers is actually mounted with reachable paths.
2. Anything skipped is recorded on ``app.state.skipped_routers``, logged at
   WARNING with a greppable marker, and accounted for in the registry.

If a router module breaks again, these fail loudly instead of quietly serving
404s.
"""

from __future__ import annotations

import logging

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from gated_communities.api.main import (
    BASE_ROUTER_MODULES,
    REQUIRED_ROUTERS,
    ROUTER_REGISTRY,
    register_all_routers,
)
from gated_communities.main import app


def effective_paths(target: FastAPI) -> set[str]:
    """Return every mounted path, honouring include prefixes.

    FastAPI >= 0.140 keeps included routers as ``_IncludedRouter`` entries
    instead of flattening them into ``app.routes``, so the prefix has to be
    resolved by walking the include context. Walking rather than reading
    ``app.routes`` directly keeps this independent of that FastAPI version
    detail.
    """
    paths: set[str] = set()

    def walk(routes, prefix: str = "") -> None:
        for entry in routes:
            original = getattr(entry, "original_router", None)
            if original is not None:
                walk(original.routes, prefix + entry.include_context.prefix)
            elif isinstance(entry, APIRoute):
                paths.add(prefix + entry.path)

    walk(target.router.routes)
    return paths


@pytest.fixture(scope="module")
def registry_app() -> FastAPI:
    """A bare app with only register_all_routers applied."""
    target = FastAPI()
    register_all_routers(target)
    return target


# ---------------------------------------------------------------------------
# The registry itself must stay well-formed
# ---------------------------------------------------------------------------


def test_router_registry_entries_are_module_attr_pairs():
    """Guards the exact regression: flat strings iterated as 2-tuples.

    A ``_REGISTRY`` of bare module names makes ``for module_name, router_attr``
    raise ValueError/NameError and breaks *all* route registration.
    """
    assert ROUTER_REGISTRY, "router registry must not be empty"

    malformed = [
        entry
        for entry in ROUTER_REGISTRY
        if not (isinstance(entry, tuple) and len(entry) == 2 and all(entry))
    ]
    assert not malformed, (
        "ROUTER_REGISTRY entries must all be (module, router_attr) 2-tuples; "
        f"got malformed entries: {malformed!r}"
    )


def test_router_registry_has_no_duplicate_targets():
    seen: set[str] = set()
    duplicates = {
        key
        for key in (f"{m}.{a}" for m, a in ROUTER_REGISTRY)
        if key in seen or seen.add(key)  # type: ignore[func-returns-value]
    }
    assert not duplicates, f"duplicate registry targets: {sorted(duplicates)}"


# ---------------------------------------------------------------------------
# Required routers must actually be mounted
# ---------------------------------------------------------------------------


def test_app_mounts_more_than_the_nine_base_routers(registry_app):
    """register_all_routers must add routers beyond the 9 mounted in main.py.

    A bare count is not enough on its own (the skip-swallowing bug would still
    inflate it), so this pairs with the required-router assertions below.
    """
    mounted = len(registry_app.router.routes)
    assert mounted > len(BASE_ROUTER_MODULES), (
        f"register_all_routers mounted {mounted} routers, expected more than the "
        f"{len(BASE_ROUTER_MODULES)} base routers — the registry is not being applied"
    )
    assert len(BASE_ROUTER_MODULES) == 9, (
        f"expected 9 base routers in gated_communities.main, got "
        f"{sorted(BASE_ROUTER_MODULES)}"
    )


@pytest.mark.parametrize("router_name", REQUIRED_ROUTERS)
def test_required_router_is_in_the_registry(router_name):
    """Every required router must actually be listed in ROUTER_REGISTRY.

    Without this, dropping a required entry from the registry would go unnoticed
    whenever the same router is *also* mounted directly in main.py (all of
    health/communities/members/moderation are), because the endpoints still
    respond and the skip set stays empty.
    """
    registry_modules = {m for m, _ in ROUTER_REGISTRY}
    assert router_name in registry_modules, (
        f"required router {router_name!r} is missing from ROUTER_REGISTRY — "
        "register_all_routers will never mount it"
    )


@pytest.mark.parametrize("router_name", REQUIRED_ROUTERS)
def test_required_router_is_mounted_by_the_registry(registry_app, router_name):
    """register_all_routers on a bare app must mount each required router.

    Checking the registry-only app (not the full app) proves this function is
    responsible for the mount, independent of main.py's direct includes.
    """
    skipped = registry_app.state.skipped_routers
    offenders = [k for k in skipped if k.split(".")[0] == router_name]
    assert not offenders, (
        f"required router {router_name!r} failed to mount: {offenders} — "
        f"{[skipped[o] for o in offenders]}"
    )
    # It must be mounted by *this* app: at least one registry entry is present.
    assert registry_app.router.routes, "registry app has no mounted routers"


@pytest.mark.parametrize("router_name", REQUIRED_ROUTERS)
def test_required_router_is_not_skipped(router_name, registry_app):
    """No router in REQUIRED_ROUTERS may be in the skipped set."""
    skipped = getattr(registry_app.state, "skipped_routers", {})
    offenders = [key for key in skipped if key.split(".")[0] == router_name]
    assert not offenders, (
        f"required router {router_name!r} failed to mount: {offenders} — "
        f"{[skipped[o] for o in offenders]}"
    )


@pytest.mark.parametrize(
    ("router_name", "expected_paths"),
    [
        ("health", ("/health",)),
        ("communities", ("/communities",)),
        ("members", ("/members",)),
        ("moderation", ("/moderation/queue",)),
        ("tiers", ("/tiers",)),
    ],
)
def test_required_router_serves_expected_paths(
    router_name, expected_paths, registry_app
):
    """The full app must serve the known-good endpoints for these routers."""
    mounted = effective_paths(app)
    missing = [p for p in expected_paths if p not in mounted]
    assert not missing, (
        f"router {router_name!r} is registered but its endpoints are absent from "
        f"the app: {missing}"
    )


@pytest.mark.parametrize(
    "path",
    [
        "/health",
        "/communities",
        "/members",
        "/moderation/queue",
        "/tiers",
    ],
)
def test_known_good_endpoint_is_routed_not_404(path):
    """End-to-end guard: required endpoints are routed rather than 404.

    ``raise_server_exceptions=False`` keeps a 500 (a real handler bug) a
    response instead of an exception, so this asserts precisely what it claims:
    the route exists. 401/422/500 are all fine — 404 means silent non-mount.
    """
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(path)

    assert response.status_code != 404, (
        f"{path} returned 404 — its router silently failed to mount "
        f"(skipped: {sorted(app.state.skipped_routers)})"
    )


# ---------------------------------------------------------------------------
# Skips must be observable, never swallowed
# ---------------------------------------------------------------------------


def test_skipped_routers_are_recorded_on_app_state(registry_app):
    """Skips land on app.state.skipped_routers as {module.attr: reason}."""
    skipped = getattr(registry_app.state, "skipped_routers", None)
    assert isinstance(skipped, dict), (
        "register_all_routers must record skips on target.state.skipped_routers "
        "so CI can observe them"
    )
    for key, reason in skipped.items():
        assert isinstance(key, str) and "." in key, f"malformed skip key: {key!r}"
        assert isinstance(reason, str) and reason, f"empty reason for skip: {key!r}"


def test_register_all_routers_returns_skip_mapping(registry_app):
    """The return value and app state agree, so callers need not guess."""
    returned = register_all_routers(FastAPI())
    assert isinstance(returned, dict)
    assert set(returned) == set(registry_app.state.skipped_routers)


def test_skipped_keys_all_belong_to_the_registry(registry_app):
    """Every skip corresponds to a registered router — no stray bookkeeping."""
    known = {f"{m}.{a}" for m, a in ROUTER_REGISTRY}
    unknown = set(registry_app.state.skipped_routers) - known
    assert not unknown, f"skipped routers not present in ROUTER_REGISTRY: {sorted(unknown)}"


def test_skip_is_logged_at_warning_with_greppable_marker(caplog):
    """A skip emits ROUTER_MOUNT_SKIPPED at WARNING so CI logs can grep it."""
    import importlib

    real_import_module = importlib.import_module
    broken = "gated_communities.api.__router_regression_probe__"

    def fake_import_module(name, package=None):
        if name == broken:
            raise ImportError("probe: simulated missing dependency")
        return real_import_module(name, package)

    probe_registry = ROUTER_REGISTRY + ((broken.split(".")[-1], "router"),)

    target = FastAPI()
    with caplog.at_level(logging.WARNING):
        # Reuse the real loop by monkeypatching the registry the function reads.
        import gated_communities.api.main as api_main

        original_registry = api_main.ROUTER_REGISTRY
        original_import = importlib.import_module
        api_main.ROUTER_REGISTRY = probe_registry
        importlib.import_module = fake_import_module
        try:
            skipped = register_all_routers(target)
        finally:
            api_main.ROUTER_REGISTRY = original_registry
            importlib.import_module = original_import

    assert f"{broken.split('.')[-1]}.router" in skipped, (
        "the broken router should have been skipped, not mounted"
    )
    messages = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    matching = [m for m in messages if "ROUTER_MOUNT_SKIPPED" in m]
    assert matching, (
        "skipping a router must log ROUTER_MOUNT_SKIPPED at WARNING; "
        f"captured warnings: {messages}"
    )
    assert any("simulated missing dependency" in m for m in matching)


def test_working_router_is_not_reported_as_skipped(registry_app):
    """Sanity check: a healthy router must not appear in the skip set."""
    skipped = registry_app.state.skipped_routers
    for router_name in ("health", "badges", "webhooks"):
        offenders = [k for k in skipped if k.split(".")[0] == router_name]
        assert not offenders, f"{router_name} should mount cleanly, got {offenders}"


def test_registry_only_app_and_real_app_both_expose_skips():
    """Both the bare registry app and the real app expose skip state."""
    assert hasattr(app.state, "skipped_routers")
    assert isinstance(app.state.skipped_routers, dict)


# ---------------------------------------------------------------------------
# A broken module must not take down the rest of the API
# ---------------------------------------------------------------------------


def test_one_broken_module_does_not_block_healthy_routers():
    """The resilience behaviour still holds: healthy routers still mount."""
    import importlib

    import gated_communities.api.main as api_main

    real_import_module = importlib.import_module
    broken = "gated_communities.api.__router_resilience_probe__"

    def fake_import_module(name, package=None):
        if name == broken:
            raise ImportError("probe: simulated missing dependency")
        return real_import_module(name, package)

    target = FastAPI()
    original_registry = api_main.ROUTER_REGISTRY
    api_main.ROUTER_REGISTRY = (("health", "health_router"), (broken.split(".")[-1], "router"))
    importlib.import_module = fake_import_module
    try:
        skipped = register_all_routers(target)
    finally:
        api_main.ROUTER_REGISTRY = original_registry
        importlib.import_module = real_import_module

    assert f"{broken.split('.')[-1]}.router" in skipped
    assert "/health" in effective_paths(target), (
        "a broken sibling must not prevent healthy routers from mounting"
    )


def test_every_registry_entry_is_either_mounted_or_skipped(registry_app):
    """Full accounting: no registry entry may vanish without a trace."""
    mounted_modules = {
        m for m, _ in ROUTER_REGISTRY
        if m not in {k.split(".")[0] for k in registry_app.state.skipped_routers}
    }
    accounted_for = mounted_modules | {
        k.split(".")[0] for k in registry_app.state.skipped_routers
    }
    assert accounted_for == {m for m, _ in ROUTER_REGISTRY}, (
        "every registry entry must be mounted or explicitly skipped"
    )