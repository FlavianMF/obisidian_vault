---
title: Confirmar Qual Worktree Está Sendo Testada Antes de Diagnosticar
type: pattern
tags: [agentic-ai, git, worktree, debugging, dev-workflow]
created: 2026-09-02
provenance: capella_llm_window
project: capella_llm_window
---

# Confirmar Qual Worktree Está Sendo Testada Antes de Diagnosticar

## Contexto

Um agente (Claude Code) trabalhando num repo que mantém várias `git
worktree` vivas em paralelo (uma por branch/feature em desenvolvimento)
recebeu um relato de "ainda não funciona" do usuário. Gastou uma rodada
inteira de investigação (via `git reflog`, `grep` no código, evidência
real, não achismo) concluindo que a checkout principal do usuário estava
desatualizada — sem nenhum dos commits recentes. Diagnóstico tecnicamente
correto... só que sobre o lugar errado: o usuário corrigiu "na verdade eu
estou testando o que está na worktree" — ele testava uma worktree
secundária diferente, não a checkout principal assumida.

## Padrão

Verificar evidência (reflog, grep, git log) é necessário mas não
suficiente — precisa verificar contra o **alvo certo** também. Num
projeto com múltiplas worktrees paralelas, o ambiente de teste ao vivo do
usuário (aqui, o workspace do Eclipse rodando "Run As Eclipse
Application") pode apontar pra qualquer uma delas, e isso não é fixo —
muda entre sessões, e às vezes dentro da mesma sessão.

Antes de investir numa investigação de "por que não funciona" que assume
qual checkout está sendo testado, perguntar ou confirmar explicitamente
qual diretório/branch é o alvo real. Um diagnóstico tecnicamente perfeito
sobre o lugar errado ainda desperdiça uma rodada inteira e gera confusão
adicional.

## Quando aplicar

Qualquer projeto/sessão de agente onde: (a) existem múltiplos checkouts/
worktrees/branches do mesmo repo vivos ao mesmo tempo, e (b) o usuário
reporta comportamento "ainda errado" depois de uma mudança que deveria
ter corrigido algo. Confirmar o alvo de teste é o primeiro passo, antes
de reabrir a investigação técnica do zero.

## 🔗 Conexões
- [[Campo de Settings Só Deve Ser Editável Se Aplicar de Verdade]]
