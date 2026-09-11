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
  no submodule, no pointer to bump. A third behavior detects the active
  harness's convention file (CLAUDE.md, AGENTS.md, .cursorrules, etc.) and
  offers to bootstrap it with a proven dev-workflow methodology (worktrees,
  test scoping, CI/CD reporting, versioning/release automation) distilled
  from the vault — always asking before writing, never autonomous. A legacy
  per-project submodule mode (docs/second_brain/) remains available for the
  rare case a repo needs an isolated pinned snapshot. Use when: user says
  "connect the second brain / vault", "sync my notes", "update the vault",
  "bootstrap this project's workflow", "add dev methodology to CLAUDE.md";
  mentions "obsidian vault"; OR — auto-trigger — you need prior
  context/patterns before starting a task, you are about to finish a coding
  task, or you're starting work in a project with no recognizable
  workflow-methodology section yet, in any project.
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

## Behavior 2 — Autonomous Doc Freshness + Vault Sync

**Two cadences, not one. Do both without asking for confirmation** — that's an
explicit user decision, not an oversight.

> **A nota é parte do entregável, não um artefato posterior.** Uma tarefa não está
> concluída enquanto a documentação que descreve o que você mexeu não voltar a ser
> verdadeira. Nota desatualizada não é dívida: é **bug**, porque mente com a
> autoridade de um documento — pior que nota nenhuma.

### 2a — Ao terminar CADA tarefa: varrer as notas do projeto

Trigger: você está prestes a declarar uma tarefa concluída, em qualquer projeto.
Antes de dizer "pronto":

1. **Liste o que tocou** — módulo, ferramenta, arquivo, versão, status de proposta,
   decisão. Essa lista é a entrada dos greps abaixo; não exige julgamento nenhum.
2. **Procure quem afirma algo sobre isso.** Caçar os *marcadores de estado*, não o
   assunto — é o que transforma julgamento em busca:
   ```bash
   grep -rniE "pendente|não implementado|ainda não|falta|TODO|planejado|aguardando|previsto" \
     docs/ notes/ README.md CLAUDE.md 2>/dev/null
   ```
   Mais um grep pelos nomes próprios do que mudou. Atenção a **contagens e versões**
   ("13 tools", "v0.1.0", "8 de 11") — apodrecem sem nenhuma palavra-marcador perto.
3. **Cada acerto: ainda é verdade?** Se não, corrija **no mesmo ciclo de trabalho** —
   não vira item de backlog, não vira "depois eu arrumo".
4. **Carimbe a verificação** em afirmação de estado: data + como foi checada
   (`verified: AAAA-MM-DD via git log`). Sem carimbo, a obsolescência é invisível.
5. **Relate ao usuário o que foi atualizado** — e o que foi checado e continuava certo.

Isto cobre a documentação **do projeto**, que é onde a mentira nasce, porque anda colada
ao código. O vault sozinho não pegaria: o incidente que originou esta regra foi em
`notes/analysis/` de um projeto, não aqui dentro.

### 2b — Ao final da SESSÃO: sincronizar com o vault

1. Se você aprendeu um padrão, decisão ou armadilha generalizável, redija/atualize uma
   nota (tipicamente em `20_Permanent_Notes/`) com o frontmatter padrão (ver abaixo),
   `provenance: <este-projeto>`.
2. **Propague a invalidação também aqui**: `grep` nos manifests
   (`00_META/manifests/by_type/*.md`) pelos termos que você tocou e corrija as notas do
   vault que a mudança tornou falsas — o passo é simétrico ao 2a, não só aditivo.
3. Rode:
   ```
   python3 ~/.claude/skills/second-brain-sync/scripts/vault_sync.py \
     --vault-path ~/obsidian_vault \
     --note "20_Permanent_Notes/<Your Note>.md" \
     --project-name <this-project-name> \
     --message "<concise commit message>"
   ```
   Isso faz `pull --ff-only`, regenera manifests, stageia só as notas passadas + os
   manifests que mudaram, commita e dá push no `master` do vault. Recusa rodar se o
   vault tiver arquivos sujos não declarados — então passe **todas** as notas novas na
   mesma chamada (`--note` é repetível).

   Caminhos com espaço/acento: monte a lista em Python e chame `subprocess.run([...])`.
   `git status --porcelain` envolve caminhos com espaço em aspas **mesmo** com
   `core.quotePath=false` — ver a nota
   `git status --porcelain Quota Caminhos com Espaço Mesmo com quotePath=false`.

Nada a fazer no projeto atual além disso — sem ponteiro pra bumpar. Como todo projeto lê
e escreve o mesmo `~/obsidian_vault`, o resultado fica visível em todo lugar na hora.

## Behavior 3 — Project Workflow Bootstrap (Ask-First)

Plants proven dev-workflow discipline (worktrees, test scoping, CI/CD reporting,
versioning/release automation) into a project's harness convention file. Unlike
Behavior 2, **this never writes without asking first** — even when the trigger was
automatic.

1. **Detect harness convention file(s).** This skill only runs inside Claude Code, so
   the default target is always `CLAUDE.md`. Also scan the project root for any other
   file from this table already present — if one exists, it's in scope too, since a
   project can serve more than one harness:

   | harness | convention file |
   |---|---|
   | Claude Code | `CLAUDE.md` |
   | Codex / generic agents | `AGENTS.md` |
   | Cursor | `.cursor/rules/` or `.cursorrules` |
   | Windsurf | `.windsurfrules` |
   | Cline | `.clinerules` |
   | Gemini CLI | `GEMINI.md` |

2. **Trigger**: starting work in a project where no workflow-methodology section has
   been detected yet this session, OR an explicit user request. Check whether the
   target file(s) already have a recognizable workflow section (a stable heading, e.g.
   `## Dev workflow`) that looks current — if so, do nothing.
3. **If missing or stale**: read
   `~/obsidian_vault/20_Permanent_Notes/Checklist de Bootstrap de Workflow de
   Desenvolvimento.md` (via Behavior 1's manifest-first lookup, then `Read` the note in
   full) and inspect the project's actual stack (build/version-manifest file) to adapt
   the checklist's six axes to this specific project. Never copy the note's
   Java/Tycho-specific instance literally into a project on a different stack.
4. **Always ask before writing** — show the drafted section, ask
   create/append/skip. No exceptions, regardless of how the trigger fired.
5. **Write**: create the file if missing; if it exists, insert/update only the
   delimited workflow section, preserving everything else in the file untouched.

No new script — this behavior is entirely prose/read-driven, like Behavior 1. There's
no git mechanics to guard (a single local file edit, no automatic commit/push).

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
- Behavior 3 never writes without explicit user confirmation, even when the trigger
  was automatic.
- Behavior 3 never overwrites a target file's existing content outside its own
  delimited workflow section.

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
the parent project. Behavior 3 only touches the harness convention file(s)
at the project root, never commits or pushes on its own — that stays part
of the project's normal flow, same as the legacy pointer-bump. Neither mode
modifies vault content the agent didn't author this session, except via the
one-time `backfill_frontmatter.py` migration pass, which is idempotent and
never overwrites an existing populated field. "stop caveman" / mode changes
elsewhere don't affect this skill's behavior — it has no persona of its own.
