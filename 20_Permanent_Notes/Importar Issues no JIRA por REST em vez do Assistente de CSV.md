---
title: Importar Issues no JIRA por REST em vez do Assistente de CSV
type: pattern
tags: [jira, rest-api, import, idempotencia, rate-limit, atlassian]
created: 2026-10-14
provenance: residencia_cariri_projects
seen_in: [residencia_cariri_projects]
verified: 2026-10-14 via pesquisa na documentação Atlassian; ainda não executado contra um JIRA real
confidence: medium
---

# Importar issues no JIRA por REST em vez do assistente de CSV

Alternativa ao CSV quando o importador do projeto limita (ver
[[Importador CSV do JIRA - Parent Aponta Issue ID do Arquivo, Não a Chave]]). **Confiança
média: vem da documentação, o script `_tools/jira-csv/importar_issues.py` ainda não rodou
contra um JIRA real.** Ele tem `--dry-run` e `--limite N` para uma primeira rodada cautelosa.

## Criação

- v2 `POST /rest/api/2/issue` aceita `description` como string em wiki markup; a v3 exige ADF.
- Story para Epic: `fields.parent = {"key": ...}`. Epic Link está descontinuado.
- Resolva o pai pelo Epic **real** do projeto (posição ou summary), nunca por chave prevista.
- Bulk create: no máximo 50 por chamada, com falhas parciais; não associe a resposta aos
  itens por índice.
- Components precisam existir antes. Labels não aceitam espaço. Projetos company-managed
  antigos ainda podem exigir Epic Name. Campo fora da tela de criação dá `field cannot be set`.
- O id do campo Story Points varia por site: `GET /rest/api/2/field`.

## Busca e idempotência

- `/rest/api/{2,3}/search` antigos foram removidos (410). Use `POST /rest/api/3/search/jql`
  com paginação `nextPageToken`/`isLast`, `fields` explícito, `maxResults` 100 e JQL sempre
  limitada ao projeto.
- Idempotência: busque todas as issues do projeto e compare o `summary` exato no cliente
  (`~` do JQL é fuzzy).

## Limite de taxa

429: respeite `Retry-After`, backoff exponencial com jitter, cerca de 4 tentativas. Só
reenvie POST quando a requisição foi rejeitada, para não duplicar.

Relacionado: [[Backlog Markdown como Fonte e CSV como Ponte para o JIRA]].
