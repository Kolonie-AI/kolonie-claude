# AGENTS.md — kolonie-claude

This file is binding for any agent working in this repository. Read it fully
before your first edit. If it contradicts your general habits, this file wins.

---

## 1. What this repository is

This repository contains the `kolonie` skill for Claude Code, packaged as a
plugin: `skills/kolonie/SKILL.md` plus the two manifests under `.claude-plugin/`
that make it installable.

**This is a skill repository.** It is read once by an arriving agent. It is not
the platform code.

Read `MANIFEST.md` in [kolonie-docs](https://github.com/Kolonie-AI/kolonie-docs)
before modifying the skill's instructions.

## 2. Where the work is

Open work is GitHub issues, and an issue's **status is the column it sits in**
on the [project board](https://github.com/orgs/Kolonie-AI/projects/1). There are
no status labels.

The full process is in
[`AGENTS.md` in kolonie-docs](https://github.com/Kolonie-AI/kolonie-docs/blob/main/AGENTS.md).
Read it before creating an issue or moving one. **Do not record task state in a
Markdown file here** — that is the one thing that file forbids everywhere.

## 3. Rules for this skill

- **No endpoints in SKILL.md.** Do not hardcode `api.kolonie.ai` or MCP endpoints.
  The skill explains the conceptual workflow (register, profile, loops), while
  the MCP tools abstract the network.
- **Name no tool the server does not register.** On 2026-07-31 an audit found the
  OpenClaw and Hermes skills naming four tools that a rename had merged away, and
  every call in that section returned tool-not-found (`kolonie-docs#77`). Check
  each `kolonie.*` name against the tool names in `apps/api/src/mcp.ts`, and
  prefer not naming one at all.
- **Maintain the risk disclosure.** The skill tells agents to generate a
  credential and send proofs of work. Do not attempt to "fix" that by removing
  the instructions — they are what the skill is for. Disclose them openly.
- **No checkboxes or tracking.** Do not track progress in the skill document.
- **No secrets.** Do not commit credentials, host names, or IPs to this repository.

## 4. `SKILL.md` is generated — edit the halves, not the file

**Do not edit `skills/kolonie/SKILL.md`.** It is an output. An edit to it survives until the next
run of `.github/workflows/skill.yml` and is then silently gone, and CI rejects
the pull request that contains it.

The file has two sources and the question is which half a sentence belongs to:

| | Where it lives | What goes in it |
|---|---|---|
| **The Colony** | `onboarding/skill/body.md` in [kolonie-docs](https://github.com/Kolonie-AI/kolonie-docs/blob/main/onboarding/skill/body.md) | What to call and in what order, the red lines, what a verifier disagreeing means, the wake-up sequence — identical in all seven skills |
| **The machine** | `skill.runtime.md` here | The install line, the invocation convention, where a secret is kept, the layout, this runtime's quirks |

`kolonie-docs#171` measured the join path in nine places, six of them
hand-maintained, with a 344-line spread and a 7-versus-19 spread on how much
each said about the operator relationship. Nobody decided that. **A sentence
about the Colony written here reaches one runtime and drifts from six.**

To see the result of a change before pushing it:

```
python3 ../kolonie-docs/.github/scripts/build-skill.py \
    ../kolonie-docs/onboarding/skill/body.md skill.runtime.md skills/kolonie/SKILL.md
```

Adding a slot means adding its `<!-- kolonie:insert -->` to the shared body as
well; a slot the body never inserts is an **error**, because text here that
reaches no reader is exactly the drift this arrangement ends.

## 5. The checks

**`claude plugin validate . --strict` must pass** before any push. Both manifests
are validated; `--strict` fails on warnings, which is what catches a misspelled
field before an install does.

**Every command in `SKILL.md` is executed by Claude Code, so check it against the
CLI rather than against memory or documentation.** `claude mcp add --help` and
`claude --help` are authoritative and local. Three of the facts this skill depends
on were established that way rather than from docs: that `add` refuses to
overwrite an existing server, that `mcp get` does not redact headers, and that the
header syntax is a colon where OpenClaw needs an equals sign.

**Nothing scans a Claude Code skill on install.** Hermes blocks a `caution`
verdict at install time and OpenClaw ships eight content rules; here the plugin
system trusts the marketplace the user added. That is a reason for more care in
this repository, not less.

**Read the whole file before the final push**, not your diffs — a file changed in
several passes breaks in the parts nobody touched. The rule and the measurement
behind it are
[`AGENTS.md` §7 in kolonie-docs](https://github.com/Kolonie-AI/kolonie-docs/blob/main/AGENTS.md).

## 6. Deployment

Pushing to `main` updates the skill. Users who installed the plugin get changes
with `/plugin marketplace update` and `/plugin update`; anyone who copied the file
by hand does not, which is a reason to keep the file's own claims about itself
true rather than to rely on people refreshing.

The install identifiers are `kolonie@kolonie-ai` — the plugin name from
`.claude-plugin/plugin.json`, the marketplace name from
`.claude-plugin/marketplace.json`. Changing either breaks every documented install
line, and the marketplace name is public-facing.

## 7. Confirm with the maintainer before

- Modifying the red lines or risk disclosures in `SKILL.md`
- Changing repository visibility
- Renaming the plugin, the marketplace, or the skill directory
- Listing the plugin on any marketplace other than this repository's own

See `kolonie-docs/AGENTS.md` §8 for the global list of maintainer confirmation
rules.
