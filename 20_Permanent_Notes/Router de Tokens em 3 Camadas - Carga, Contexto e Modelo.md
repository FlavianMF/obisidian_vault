---
title: Router de Tokens em 3 Camadas - Carga, Contexto e Modelo
type: decision
tags: [tokens, claude-code, second-brain, router]
created: 2026-10-22
provenance: obsidian_vault
seen_in: [obsidian_vault]
confidence: low
scope: global
verified: 2026-10-22 via candidato do agente em obsidian_vault, não reproduzido na revisão
---

# Router de Tokens em 3 Camadas - Carga, Contexto e Modelo

## Decisão

Reduzir o gasto de tokens em três camadas, na ordem do ganho esperado:

1. **Carga:** desligar plugins por projeto (`plugins-project.sh`).
2. **Contexto:** limiar de silêncio do hint do second brain, em cobertura 0,36. Abaixo dele o hint não injeta nada.
3. **Modelo:** sugestão de delegação por regex no `UserPromptSubmit` (`sb-router.sh`).

O router nasce **ativo**. O kill-switch é `SB_ROUTER=0` ou a existência de um arquivo `DISABLED`.

## Critério de saída

Se não houver queda medida de tokens, desligar o router.

## O que NÃO funcionou

Nada foi medido ainda: a nota registra a decisão e o critério de saída, não um resultado. Até a medição existir, vale `confidence: low`.
