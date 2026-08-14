#!/usr/bin/env python3
"""The packaging check, seen failing before it is trusted when it passes.

`check-red-lines.yml` in `kolonie-docs` states the rule: a check nobody has
watched fail correctly is a check nobody should believe when it is green. This
one guards a credential, so the rejection cases matter more than the pass — a
version of it that accepted everything would be silently green forever, and the
thing it was protecting would ship.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "check_packaged_server", HERE.parent / "scripts" / "check-packaged-server.py"
)
assert spec is not None and spec.loader is not None
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)

GOOD = {
    "mcpServers": {
        "kolonie": {
            "type": "http",
            "url": "https://mcp.kolonie.ai/",
            "headers": {"Authorization": "Bearer ${KOLONIE_API_KEY}"},
        }
    }
}

failures = 0


def case(name: str, manifest: dict | None, expected: bool, extra: dict[str, str] = {}) -> None:
    """One tree, built and checked. `expected` is whether it should pass."""
    global failures
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        if manifest is not None:
            (root / ".mcp.json").write_text(json.dumps(manifest), encoding="utf-8")
        for relative, content in extra.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        passed = check.main(root) == 0
        if passed is expected:
            print(f"ok   {name}")
        else:
            print(f"FAIL {name}: expected {'pass' if expected else 'failure'}")
            failures += 1


case("the shipped manifest is accepted", GOOD, True)

case("a missing .mcp.json is a failure", None, False)

# The one this check exists for. An agent debugging a 401 replaces the
# reference with its own key, and without this the tree is green.
case(
    "a real key in the header is refused",
    {
        "mcpServers": {
            "kolonie": {
                "type": "http",
                "url": "https://mcp.kolonie.ai/",
                "headers": {"Authorization": "Bearer kol_" + "a" * 32},
            }
        }
    },
    False,
)

# A reference with something appended is a value assembled from the variable,
# not a reference. It has to fail or the pattern above forgives the case above.
case(
    "a reference with anything appended is refused",
    {
        "mcpServers": {
            "kolonie": {
                "type": "http",
                "url": "https://mcp.kolonie.ai/",
                "headers": {"Authorization": "Bearer ${KOLONIE_API_KEY}-live"},
            }
        }
    },
    False,
)

case(
    "a server that is not https is refused",
    {"mcpServers": {"kolonie": {"type": "http", "url": "http://mcp.kolonie.ai/"}}},
    False,
)

# A key pasted into a document rather than into the header — the same leak by a
# different door.
case(
    "a key pasted into a shipped file is refused",
    GOOD,
    False,
    {"skills/kolonie/SKILL.md": "worked with kol_" + "b" * 40 + "\n"},
)

# And the sentence the skill actually contains, which names the prefix without
# carrying a key. A check that failed on this would be one nobody could keep.
case(
    "prose about the kol_ prefix is not a key",
    GOOD,
    True,
    {"skills/kolonie/SKILL.md": "Every key the Colony issues begins `kol_`.\n"},
)

print("\nall cases behaved" if failures == 0 else f"\n{failures} case(s) did not")
sys.exit(1 if failures else 0)
