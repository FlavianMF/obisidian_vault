---
title: Frontmatter Schema
type: meta
tags: [meta, agentic-ai, knowledge-base, schema]
created: 2026-08-09
provenance: manual
---

# 🧬 Frontmatter Schema

Esta nota é a fonte canônica do schema de frontmatter usado por todas as notas
deste vault. `generate_manifests.py` e `backfill_frontmatter.py` (skill
`second-brain-sync`) leem e escrevem exatamente estes campos — se você editar
este schema, atualize os dois scripts junto.

## 🏛️ Campos

| campo | obrigatório | notas |
|---|---|---|
| `title` | sim | legível por humano, pode diferir do nome do arquivo |
| `type` | sim | `meta, pattern, decision, concept, trap, project, literature, moc, inbox, template, unclassified` |
| `tags` | sim | lista, pode ser `[]` |
| `created` | sim | `YYYY-MM-DD` |
| `provenance` | recomendado | `manual` para notas escritas à mão; nome do projeto de origem para notas destiladas por agente |
| `project` | opcional | texto livre, já usado ad hoc em notas de projeto |

`path` nunca é campo de frontmatter — é metadado computado, só existe nos
manifests (`00_META/manifests/`).

## 🔍 Como `type` é inferido no backfill

Para notas sem frontmatter (`backfill_frontmatter.py`), `type` é derivado da
pasta:

| pasta | `type` |
|---|---|
| `20_Permanent_Notes/` | `concept` |
| `90_Assets/` | `template` |
| `30_MOCs/` | `moc` |
| `40_Projects/` | `project` |
| `00_Inbox/` | `inbox` |
| `10_Literature_Notes/` | `literature` |
| `00_META/` | `meta` |
| arquivo com nome `Skill - *.md` | `pattern` (independe da pasta) |
| qualquer outra | `unclassified` |

O backfill nunca sobrescreve um campo já preenchido — só completa o que falta.

## 🔗 Conexões
- [[Skill - Sincronização de Conhecimento Recursiva]]
- [[00_META/Agent-Instruction]]
