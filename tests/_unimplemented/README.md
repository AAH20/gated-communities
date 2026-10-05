# Quarantined tests — unimplemented APIs

These test files were moved here because they import modules that **do not exist**
in this repository, so they could never run. They were collected by pytest and
failed at import, breaking CI.

## Why they exist

They were written against an intended package layout that was never implemented:

| File | Imports | Status |
|---|---|---|
| `test_connection_phantom.py` | `src.websocket.connection` | no such module |
| `test_presence_phantom.py` | `src.websocket.connection`, `src.websocket.presence` | no such modules |
| `test_ws_messages_phantom.py` | `src.websocket.connection`, `src.websocket.messages` | no such modules |
| `test_access_control_unit_phantom.py` | `src.access_control` | no such module |
| `test_reputation_system_unit_phantom.py` | `src.reputation` | no such module |
| `test_tier_management_unit_phantom.py` | `src.agents.gated_communities.tier_management` (`TierManager`) | `TierManager` does not exist anywhere in `src/` |

The package is `gated_communities` under `src/`, so `src.*` is never a valid
import root. The real equivalents that *do* exist are:

- access control → `gated_communities.agents.access_control`
- reputation → `gated_communities.agents.reputation_system`
- tier management → `gated_communities.agents.tier_management`
- websockets → `gated_communities.api.websocket`, `gated_communities.api.websockets`

## Files here are not collected

The directory name starts with `_`, so pytest does not collect it. The files are
kept as a record of the intended API surface.

## To restore

Either implement the missing modules, or rewrite each test against the real
modules listed above and move it back under `tests/`.