---
title: Skill: Fluxo de Trabalho de Feature Branch
type: pattern
tags: [agentic-ai, git, workflow, automation, worktree, conventional-commits]
created: 2026-05-21
provenance: manual
project: orbita-platform
---

# Skill: Fluxo de Trabalho de Feature Branch

Comportamento autônomo para gestão de código e versionamento durante o desenvolvimento de
novas funcionalidades.

## 🤖 Comportamento Esperado

1.  **Criação de branch**: branch dedicada, nunca trabalho direto na branch de integração.
2.  **Commits de processo**: commits incrementais a cada sub-etapa concluída (ex.: "define
    schemas", "impl logic", "add tests"), em [[caveman-commit|Conventional Commits]].
3.  **Finalização**: **nunca mesclar automaticamente**. O agente deixa a branch pronta e
    informa o usuário.

## Duas formas, e quando cada uma vale

**Branch simples — `feat/<nome>` / `fix/<nome>`** (`git checkout -b feat/sua-feature`).
Serve quando há uma sessão por vez no repositório e a validação é o próprio CI.

**Worktree dedicada — `worktree-<escopo>`** (`git worktree add <path> -b worktree-<escopo>`).
É a forma obrigatória quando **várias sessões, agênticas ou humanas, podem estar no mesmo
repositório ao mesmo tempo** — commit direto num checkout compartilhado é colisão silenciosa.
Foi a prática que se firmou no `orbita-platform` ao longo de uma fase inteira, junto com:

- **uma worktree por etapa do plano de fase**, relação 1:1:1:1 com PR e nota de conclusão
  ([[Plano de Fase em Etapas Mescláveis]]);
- **escopo do commit = a etapa**, não o arquivo: `feat(fase2-e10):`, `docs(fase2-e9b):`,
  `fix(etapa11):`. Sufixo `(Qn)` quando o commit implementa a resposta da pergunta numerada
  `n` feita ao usuário naquela sessão;
- **PR e merge são do usuário**, depois de ele validar o código da worktree rodando ao vivo
  (num slot de homologação com dados reais, quando existe). O agente não mescla nem
  reinicia serviço ao vivo — o que ele considera pronto e o usuário reprova ao ver na tela
  é a categoria de retrabalho que essa regra elimina;
- antes de mesclar (quando o usuário pedir), **conferir se outra sessão commitou na mesma
  branch** (`git log --oneline` contra o ponto de criação da worktree) em vez de presumir
  exclusividade.

Armadilha irmã: o ambiente de execução/teste do usuário pode estar apontando para qualquer
uma das worktrees — ver
[[Confirmar Qual Worktree Está Sendo Testada Antes de Diagnosticar]]. Para empurrar uma
branch que outra sessão está ocupando, [[Push Pra Branch Ocupada Via Branch Temporária]].

## 🔗 Conexões
- [[Checklist de Bootstrap de Workflow de Desenvolvimento]]
- [[Plano de Fase em Etapas Mescláveis]]
- [[Confirmar Qual Worktree Está Sendo Testada Antes de Diagnosticar]]
- [[Push Pra Branch Ocupada Via Branch Temporária]]
- [[Engenharia de Sistemas Agêntica]]
- [[00_META/Agent-Instruction]]
