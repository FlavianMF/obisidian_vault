---
title: Push Pra Branch Ocupada Via Branch Temporária
type: pattern
tags: [git, worktree, agentic-ai, dev-workflow]
created: 2026-09-02
provenance: capella_llm_window
project: capella_llm_window
---

# Push Pra Branch Ocupada Via Branch Temporária

## Contexto

Um agente (Claude Code) rodando isolado numa `git worktree` própria
precisou atualizar uma branch compartilhada (`develop`) que já estava com
checkout ativo em outro lugar (a checkout principal do usuário, ou outra
worktree). `git checkout develop` nessa situação falha
(`already checked out`) — e mesmo que não falhasse, mexer no HEAD de uma
worktree que não é sua é arriscado (pode confundir sessão paralela do
usuário ou de outro agente).

## Padrão

Não pedir pro usuário liberar a branch, nem tentar contornar o isolamento.
Construir o commit numa branch local com **outro nome**, e empurrar esse
conteúdo pra branch real via refspec `origin/<temp>:<branch-real>`:

```bash
git fetch origin
git checkout -b tmp-sync-develop origin/develop
git merge origin/master --no-edit   # ou o commit/merge que for necessário
git push origin tmp-sync-develop:develop
git checkout <minha-branch-original>
git branch -d tmp-sync-develop
```

Isso atualiza a branch remota diretamente, sem nunca dar checkout no nome
dela localmente — o `already checked out` nunca entra em jogo porque o
git só reclama do **nome local**, não do conteúdo empurrado pro remoto.

## Quando aplicar

- Qualquer sessão de agente isolada em worktree que precise commitar
  direto numa branch compartilhada (não via PR) e essa branch está em uso
  em outro checkout/worktree.
- Antes do push final, confirmar se o repo tem proteção de branch ativa
  (`gh api repos/<owner>/<repo>/branches/<branch>/protection`) — se tiver,
  esse fluxo não serve pra empurrar direto; o conteúdo da branch temporária
  precisa virar PR normal em vez do último `git push origin <temp>:<real>`.
- Diff arriscado ou não-trivial: confirmar com o usuário antes de dar push
  direto numa branch compartilhada, mesmo usando essa técnica — ela resolve
  o problema mecânico do checkout ocupado, não substitui a decisão de
  "posso empurrar isso sem PR?".

## 🔗 Conexões
- [[Tag de Release Não Volta Pra Develop Sozinha]]
- [[Confirmar Qual Worktree Está Sendo Testada Antes de Diagnosticar]]
