---
name: second-brain-sync
description: >
  Connects Claude Code to a personal Obsidian "second brain" vault as a single
  global instance, cloned once at ~/obsidian_vault (the skill itself lives
  inside that repo and is exposed globally via the ~/.claude/skills symlink —
  no per-project setup needed). Two core behaviors: (1) read the vault via its
  generated manifests (00_META/manifests/) via grep instead of opening every
  note or relying on Dataview blocks, which are inert outside the Obsidian
  app, (2) autonomously distill and push new patterns/decisions/traps to the
  vault at the end of any dev task, in any project — no confirmation needed,
  no submodule, no pointer to bump. A legacy per-project submodule mode
  (docs/second_brain/) remains available for the rare case a repo needs an
  isolated pinned snapshot. Use when: user says "connect the second brain /
  vault", "sync my notes", "update the vault"; mentions "obsidian vault"; OR —
  auto-trigger — you need prior context/patterns before starting a task, or
  you are about to finish a coding task, in any project.
---

Connects to a personal Obsidian vault (a single global clone, not a
per-project submodule), reads it efficiently, and keeps it updated
autonomously as work happens — in any project, with zero per-project setup.

## Vault location

Canonical instance: `~/obsidian_vault` — a plain git clone of
`https://github.com/FlavianMF/obisidian_vault.git`, checked out on `master`.
Bootstrapped once by `dotfiles/install.sh`, and the same path on every
project on this machine. This skill's own source lives inside that repo at
`00_META/skills/second-brain-sync/`, exposed globally via the
`~/.claude/skills/second-brain-sync` symlink — editing the skill here ships
it to every project immediately, no per-project action required.

Do not use a `docs/second_brain/` path unless the Legacy mode below was
explicitly requested.

## Prerequisites

- `~/obsidian_vault` exists as a plain git clone, checked out on `master`
  (not detached HEAD).
- `python3` on PATH (scripts are stdlib-only, no pip install needed).
- `gh` authenticated with an HTTPS git credential helper wired into
  `~/.gitconfig` (`credential.https://github.com.helper`) so push works without
  extra SSH setup.

## Behavior 1 — Manifest-First Read

Before reading vault content:

1. Read `~/obsidian_vault/00_META/manifests/INDEX.md` — small, always safe to read in full.
2. **`grep` — never `Read` in full** — the relevant `~/obsidian_vault/00_META/manifests/by_type/<type>*.md`
   file(s) for your keyword. The glob covers shards automatically if a type has
   grown past the shard threshold. This keeps context cost proportional to how
   many rows match, not to how large the vault has grown.
3. Open (Read tool) only the shortlisted full notes from the grep matches.
4. Inside a note you may follow one hop of its `[[wikilinks]]` for traceability
   (existing vault convention) — don't re-scan manifests recursively for every link.
5. If Gemini-CLI-style `obsidian_rag_query`/`obsidian_read_note`/`obsidian_link_audit`
   tools happen to be available (they aren't in Claude Code), those remain
   preferred per the vault's own `Agent-Instruction.md` — this behavior is the
   concrete fallback for agents that don't have them.

## Behavior 2 — Autonomous End-of-Task Sync

Trigger: you are finishing a dev task in any project.
**Do this without asking for confirmation** — that's an explicit user decision,
not an oversight.

1. If you learned a generalizable pattern, decision, or trap, draft/update a note
   (typically under `20_Permanent_Notes/`) with the standardized frontmatter
   (see below), `provenance: <this-project-name>`.
2. Run:
   ```
   python3 ~/.claude/skills/second-brain-sync/scripts/vault_sync.py \
     --vault-path ~/obsidian_vault \
     --note "20_Permanent_Notes/<Your Note>.md" \
     --project-name <this-project-name> \
     --message "<concise commit message>"
   ```
   This pulls `--ff-only`, regenerates manifests, stages only the note + any
   manifest files that actually changed, commits, and pushes to the vault's
   `master`. It refuses to run if the vault has unrelated dirty files.

That's it — no pointer to bump, nothing to change in the current project.
Because every project reads and writes the same `~/obsidian_vault`, the
result is visible everywhere immediately, not just in the project the sync
ran from.

## Frontmatter Schema

Canonical copy lives at `~/obsidian_vault/00_META/Frontmatter-Schema.md`
(so any agent reading the vault directly sees it, not just ones with this skill).

| field | required | notes |
|---|---|---|
| `title` | yes | human-readable, may differ from filename |
| `type` | yes | `meta, pattern, decision, concept, trap, project, literature, moc, inbox, template, unclassified` |
| `tags` | yes | list, may be `[]` |
| `created` | yes | `YYYY-MM-DD` |
| `provenance` | recommended | `manual` for hand-authored notes; originating project name for agent-distilled notes |
| `project` | optional | freeform, already used ad hoc |

`path` is never a frontmatter field — it's manifest-only, computed metadata.

## Guardrails

- Never `--force` push. Never rewrite vault history.
- Never `git add -A` inside the vault — only explicit paths.
- One concern per commit.
- Never delete or overwrite an existing note without a clearly superseding reason.

## Examples

Reading before answering "how did I handle Docker sandboxing before":
```
grep -il docker ~/obsidian_vault/00_META/manifests/by_type/*.md
```

Syncing a learned pattern at the end of a task:
```
python3 ~/.claude/skills/second-brain-sync/scripts/vault_sync.py \
  --vault-path ~/obsidian_vault \
  --note "20_Permanent_Notes/OAuth Refresh Token Race.md" \
  --project-name hermes_docker \
  --message "docs(vault): distill OAuth refresh race condition pattern"
```

## Legacy — Per-Project Submodule Mode (opt-in only)

Only use this if a project genuinely needs an isolated, pinned snapshot of
the vault vendored into its own repo — e.g. for distribution to an
environment that can't assume a personal `~/obsidian_vault` exists on the
machine. This is a deliberate exception, not the default: a per-project
checkout will drift from `~/obsidian_vault` over time unless someone
remembers to bump it, which is exactly the staleness problem the global mode
above exists to avoid.

1. Confirm the project is already a git repo. Do not `git init` it yourself —
   that's a separate, explicit user action.
2. Ensure `docs/` exists.
3. `git submodule add https://github.com/FlavianMF/obisidian_vault.git docs/second_brain`
4. `git config -f .gitmodules submodule.docs/second_brain.branch master`
5. **`git -C docs/second_brain checkout master`** — critical. `submodule add`
   leaves the checkout in detached HEAD at whatever commit was `origin/master`'s
   tip at add-time. Skip this and a later sync commit lands on an unreachable
   detached-HEAD commit that can't be pushed to `master`.
6. `git add .gitmodules docs/second_brain && git commit -m "chore: connect second-brain vault as submodule at docs/second_brain (legacy pinned mode)"`

If you take this path, Behaviors 1 and 2 above still apply — just substitute
`docs/second_brain` for `~/obsidian_vault` in every command, and after a
Behavior 2 sync also bump the pointer in the parent project:
```
git add docs/second_brain
git commit -m "chore: bump second_brain to <short-sha> - <summary>"
```
(Do not push the parent project — that repo's own push/PR discipline is
untouched.) Staleness of this particular checkout relative to
`~/obsidian_vault` and to any other project's own pinned checkout is then
expected and accepted, not a bug.

## Boundaries

Global mode does not touch the parent project at all — it only reads and
writes `~/obsidian_vault`. Legacy mode does not touch the parent project's
own branch/PR flow — that's governed by whatever conventions already apply
there; it only adds one local commit for the pointer bump, and never pushes
the parent project. Neither mode modifies vault content the agent didn't
author this session, except via the one-time `backfill_frontmatter.py`
migration pass, which is idempotent and never overwrites an existing
populated field. "stop caveman" / mode changes elsewhere don't affect this
skill's behavior — it has no persona of its own.
