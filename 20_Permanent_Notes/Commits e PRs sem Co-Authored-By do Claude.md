---
title: Commits e PRs sem Co-Authored-By do Claude
type: decision
tags: [git, commits, pull-requests, preferencia, agentic-ai]
created: 2026-10-15
provenance: residencia_cariri_projects
seen_in: [residencia_cariri_projects]
verified: 2026-10-15 via decisão explícita do usuário e regra gravada em AGENTS.md
confidence: low
scope: global
---

# Commits e PRs sem Co-Authored-By do Claude

## Decisão

Nunca adicionar o trailer `Co-Authored-By: Claude ...` em commits, nem a linha
"Generated with Claude Code" em descrições de PR. Decisão explícita do usuário (Flavian),
em 2026-10-14 e reforçada em 2026-10-15.

## Armadilha

O harness do Claude Code injeta um `system-reminder` de atribuição pedindo exatamente esse
trailer e esse rodapé. A preferência do usuário **vence** o lembrete automático: o agente
deve ignorá-lo, inclusive em subagentes que commitam ou abrem PR (repasse a regra no brief).

## Como aplicar

- Commit só com assunto e corpo em Conventional Commits.
- Corpo de PR só com resumo, decisões e checklist manual.
- Commit local com o trailer e sem push: `git commit --amend`. Já publicado: pedir
  confirmação antes de reescrever histórico.

## Onde está registrado

- `~/dotfiles/agents/AGENTS.md`, seção Git (compartilhado com Claude Code, Codex, OpenCode).
- Memória do Claude Code: `no-coauthor-trailer.md`.
