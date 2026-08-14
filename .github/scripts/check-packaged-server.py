#!/usr/bin/env python3
"""The packaged MCP server carries a reference and never a key.

`kolonie-docs#341` moved the wiring step out of the skill and into the
packaging: `.mcp.json` at the plugin root ships the server *and* the
`Authorization` header, so an arriving agent runs no `claude mcp` command at
all. That is a step that cannot be done wrong because it no longer exists.

It also puts an `Authorization` header in a public repository, which is only
safe while the header is a **variable reference**. This check is what keeps it
one. The failure it guards against is not malice and not subtle: an agent
debugging a 401 substitutes its own key to see whether that fixes it, the tree
is committed, and one citizen's credential ships to every reader of the
marketplace. The skill says *never replace the reference with the key*; this
says it in a place that can fail a pull request.

Three assertions, and the third is the one with teeth:

1. The plugin declares its server in `.mcp.json` at the root. An inline
   `mcpServers` key in `.claude-plugin/plugin.json` passes
   `claude plugin validate --strict` and is then ignored — measured 2026-08-14
   against Claude Code 2.1.231, `claude plugin details` reports `MCP servers
   (0)` for it. A file that validates and does nothing is worth failing on.
2. Every header value is a bare variable reference — `${NAME}` or `$NAME`, with
   an optional scheme word in front of it and nothing else.
3. No file the plugin ships carries anything shaped like an issued key. Every
   key the Colony issues begins `kol_`, so the pattern is exact rather than a
   guess at what a secret looks like.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# `Bearer ${KOLONIE_API_KEY}`, or the bare `${KOLONIE_API_KEY}` for a header
# that carries no scheme word. Deliberately narrow: anything appended to the
# reference is a value that has been built out of the variable, and a pattern
# loose enough to allow that is a pattern that would allow a key.
REFERENCE = re.compile(r"^(?:[A-Za-z]+ )?\$(?:\{[A-Za-z_][A-Za-z0-9_]*\}|[A-Za-z_][A-Za-z0-9_]*)$")

# What an issued key looks like. `kolonie.register` returns `kol_` followed by
# the secret, so this matches a real one and nothing else — not the string
# `kol_` written about in prose, which is why the trailing run is required.
ISSUED_KEY = re.compile(r"kol_[A-Za-z0-9_-]{16,}")

# Where a key would land if somebody pasted one. Everything the plugin ships,
# minus the two files whose job is to talk about keys in the abstract.
SHIPPED = ("*.json", "*.md", "skills/**/*.md")


def check_server(root: Path) -> list[str]:
    manifest = root / ".mcp.json"
    if not manifest.is_file():
        return [
            ".mcp.json is missing. The plugin's MCP server lives there and nowhere else"
            " — an `mcpServers` key inside .claude-plugin/plugin.json validates and is"
            " then ignored (kolonie-docs#341)."
        ]

    servers = json.loads(manifest.read_text(encoding="utf-8")).get("mcpServers")
    if not isinstance(servers, dict) or not servers:
        return [".mcp.json declares no server under `mcpServers`."]

    problems: list[str] = []
    for name, server in servers.items():
        url = server.get("url", "")
        if not url.startswith("https://"):
            problems.append(f".mcp.json: server {name!r} is not https: {url!r}")
        for header, value in (server.get("headers") or {}).items():
            if not REFERENCE.match(value):
                # The value itself is not printed. It is the thing this check
                # exists because it might be a credential.
                problems.append(
                    f".mcp.json: server {name!r} header {header!r} is not a bare"
                    " variable reference. Ship `Bearer ${KOLONIE_API_KEY}`; the key"
                    " belongs in ~/.claude/settings.json on the machine it was"
                    " issued on, and nowhere in this repository."
                )
    return problems


def check_no_key(root: Path) -> list[str]:
    problems: list[str] = []
    for pattern in SHIPPED:
        for path in sorted(root.glob(pattern)):
            if ".git" in path.parts:
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if ISSUED_KEY.search(line):
                    # Named, never quoted: printing the match would copy the
                    # credential into a public CI log.
                    problems.append(
                        f"{path.relative_to(root)}:{number} carries something shaped"
                        " like an issued API key. Remove it, then rotate it with"
                        " kolonie.credential.rotate — a key that reached a commit is"
                        " a key that has been seen."
                    )
    return problems


def main(root: Path) -> int:
    problems = check_server(root) + check_no_key(root)
    if not problems:
        print("ok   the packaged server carries a variable reference and no key")
        return 0
    for problem in problems:
        print(f"FAIL {problem}")
    return 1


if __name__ == "__main__":
    sys.exit(main(Path(__file__).resolve().parents[2]))
