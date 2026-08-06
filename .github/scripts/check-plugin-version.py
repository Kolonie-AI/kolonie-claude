#!/usr/bin/env python3
"""Every file that advertises this plugin's version advertises the same one.

`skill.runtime.md` is the source. `skills/kolonie/SKILL.md` inherits it by being
generated (`.github/workflows/skill.yml`), and the two manifests in
`.claude-plugin/` do not inherit it from anything — they are maintained by hand,
which is why they drifted three releases behind and a citizen had to report it
(kolonie-platform#467).

Run it from the repository root:

    python3 .github/scripts/check-plugin-version.py

Exit 0 when all four agree, 1 when they do not, naming every file and its value.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FRONTMATTER = re.compile(r"^---$(.*?)^---$", re.MULTILINE | re.DOTALL)
VERSION_LINE = re.compile(r"^version:\s*(\S+)\s*$", re.MULTILINE)


def frontmatter_version(path: Path) -> str:
    """The `version:` of the first YAML frontmatter block in a Markdown file.

    Not a YAML parse: `skill.runtime.md` opens with an HTML slot comment rather
    than `---`, so the block is found wherever it starts, and one scalar is all
    that is wanted from it.
    """
    match = FRONTMATTER.search(path.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit(f"{path}: no frontmatter block")
    version = VERSION_LINE.search(match.group(1))
    if not version:
        raise SystemExit(f"{path}: frontmatter carries no version")
    return version.group(1)


def plugin_manifest_version(path: Path) -> str:
    return json.loads(path.read_text(encoding="utf-8"))["version"]


def marketplace_version(path: Path, plugin: str) -> str:
    entries = json.loads(path.read_text(encoding="utf-8"))["plugins"]
    for entry in entries:
        if entry.get("name") == plugin:
            return entry["version"]
    raise SystemExit(f"{path}: no plugin entry named {plugin!r}")


def main(root: Path) -> int:
    source = root / "skill.runtime.md"
    expected = frontmatter_version(source)

    found = {
        str(source.relative_to(root)): expected,
        "skills/kolonie/SKILL.md": frontmatter_version(root / "skills/kolonie/SKILL.md"),
        ".claude-plugin/plugin.json": plugin_manifest_version(
            root / ".claude-plugin/plugin.json"
        ),
        ".claude-plugin/marketplace.json": marketplace_version(
            root / ".claude-plugin/marketplace.json", "kolonie"
        ),
    }

    disagree = {name: v for name, v in found.items() if v != expected}
    if not disagree:
        print(f"ok   every manifest advertises {expected}")
        return 0

    print(f"FAIL {source.name} says {expected} and these do not agree:\n")
    for name, version in found.items():
        mark = "  " if version == expected else "->"
        print(f"  {mark} {name}: {version}")
    print(
        "\nThe version in skill.runtime.md is the source. Bring the others to it —"
        "\nnever the other way round, and never by editing the generated SKILL.md,"
        "\nwhich is an output (kolonie-docs#171)."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(Path(__file__).resolve().parents[2]))
