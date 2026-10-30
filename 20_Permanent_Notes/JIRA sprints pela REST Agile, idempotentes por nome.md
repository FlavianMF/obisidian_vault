---
title: JIRA: sprints pela REST Agile, idempotentes por nome
type: pattern
tags: [pattern, residencia_cariri_projects]
created: 2026-10-30
provenance: residencia_cariri_projects
seen_in: [residencia_cariri_projects]
confidence: low
scope: global
verified: 2026-10-30 via candidato do agente em residencia_cariri_projects, não reproduzido na revisão
---

# JIRA: sprints pela REST Agile, idempotentes por nome

## Contexto
Achar board com GET /rest/agile/1.0/board?type=scrum&projectKeyOrId=K, listar sprints do board e criar só as que faltam com POST /rest/agile/1.0/sprint (nasce future, nome+originBoardId+datas). Script criar_sprints.py rodou nos 8 projetos CR* sem duplicar; nunca iniciar/fechar sem pedido.

## O que NÃO funcionou
- A preencher
