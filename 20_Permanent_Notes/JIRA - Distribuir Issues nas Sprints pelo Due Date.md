---
title: JIRA - Distribuir Issues nas Sprints pelo Due Date
type: decision
tags: [jira, sprint, residencia_cariri_projects]
created: 2026-10-22
provenance: residencia_cariri_projects
seen_in: [residencia_cariri_projects]
confidence: low
scope: global
verified: 2026-10-22 via candidato do agente em residencia_cariri_projects, não reproduzido na revisão
---

# JIRA - Distribuir Issues nas Sprints pelo Due Date

## Decisão

Distribuir as issues sem sprint nas sprints existentes **pelo Due date**, por script (`distribuir_sprints.py`), em vez de mover uma a uma.

## Como funciona

- **Seleção** por JQL via `POST /rest/api/3/search/jql`:
  `sprint is EMPTY AND statusCategory != Done AND issuetype != Epic`.
- **Regra de sprint:** a primeira sprint cujo fim seja maior ou igual ao Due date (fim de semana vai para a seguinte).
- **Épico não entra em sprint.**
- **Movimento** em lotes de 50 por `POST /sprint/{id}/issue`.
- **Rode com `--dry-run` antes** de aplicar.

## O que NÃO funcionou

Nada falhou no relato de origem, e esta revisão não reproduziu o script. A regra do fim de semana vem do resumo do candidato e não foi confirmada contra o código.

## Relacionadas

- [[Importar Issues no JIRA por REST em vez do Assistente de CSV]]
