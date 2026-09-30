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
| `provenance` | recomendado | `manual` para notas escritas à mão; nome do projeto de origem para notas destiladas por agente; `unknown` quando a origem não é recuperável (nem pelo `git log`, nem por `project:`) |
| `project` | opcional | texto livre, já usado ad hoc em notas de projeto |
| `verified` | opcional | `AAAA-MM-DD via <como foi checado>` (ex.: `2026-09-11 via git log`). **Recomendado em toda nota que afirma estado de um sistema** — versão, status de proposta, contagem, "já implementado"/"pendente". Torna a idade da afirmação visível em vez de invisível; sem ele, a obsolescência só aparece quando alguém se queima. Ver [[Documentação Desatualizada é Bug, Não Dívida]] |
| `confidence` | opcional | `low` (visto uma vez, não reproduzido), `medium` (reproduzido ou documentado upstream), `high` (confirmado em 2+ projetos ou por teste) |
| `seen_in` | opcional | lista de projetos que confirmaram a nota, ex.: `[capella_mcp, orbita-platform]`. Confirmar nota existente = acrescentar aqui, não criar nota duplicada |
| `scope` | opcional | `global` (padrão) ou `project`. Nota `project` não é candidata a promoção |

`path` nunca é campo de frontmatter — é metadado computado, só existe nos
manifests (`00_META/manifests/`).

`generate_manifests.py` busca os campos por nome (`data.get(...)`), então todo campo
opcional ausente vira coluna vazia. `confidence` e `seen_in` viram colunas dos manifests
(e `seen_in` alimenta o `session_hint.sh`); a data no início de `verified` alimenta
`--stale-report`. `scope` é só lido por agente.

**Promoção:** nota com 2+ projetos em `seen_in` é candidata a subir para a lista
MANDATÓRIO de [[00_META/Agent-Instruction]] ou para o checklist de bootstrap. Manual,
proposta ao usuário — nenhum processo faz isso sozinho.

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
