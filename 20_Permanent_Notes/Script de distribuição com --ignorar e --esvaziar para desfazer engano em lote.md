---
title: Script de distribuição com --ignorar e --esvaziar para desfazer engano em lote
type: pattern
tags: [pattern, residencia_cariri_projects]
created: 2026-10-30
provenance: residencia_cariri_projects
seen_in: [residencia_cariri_projects]
confidence: low
scope: global
verified: 2026-10-30 via candidato do agente em residencia_cariri_projects, não reproduzido na revisão
---

# Script de distribuição com --ignorar e --esvaziar para desfazer engano em lote

## Contexto
distribuir_sprints.py: --esvaziar devolve issues não concluídas da sprint ao backlog (POST /rest/agile/1.0/backlog/issue, lotes de 50) antes de redistribuir; --ignorar deixa uma sprint montada à mão fora do plano. Sempre --dry-run antes. Torna recuperação repetível em vez de comando avulso.

## O que NÃO funcionou
- A preencher
