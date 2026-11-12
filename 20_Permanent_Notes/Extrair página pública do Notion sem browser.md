---
title: "Extrair página pública do Notion sem browser"
type: permanent
created: 2026-11-10T14:33:00
moc: "Design de Interface com Agente"
tags: [notion, web-scraping, headless-browser]
source_inbox: "fdda7e67-extrair-pagina-publica-do-notion-sem-browser.md"
tier: "L1"
score: 0.731
---

# Extrair página pública do Notion sem browser

Página notion.site não renderiza em browser headless. Use POST <site>/api/v3/loadCachedPageChunkV2 com cursor paginado e user-agent curl. Busque filhos de toggles com syncRecordValuesMain.

# Extrair página pública do Notion sem browser

## Contexto
A página `notion.site` não renderiza corretamente em navegadores headless, o que dificulta a extração de dados de forma automática.

## Detalhes
Para extrair dados da página `notion.site`, é necessário usar uma abordagem baseada em API. Especificamente, pode-se utilizar o endpoint `POST <site>/api/v3/loadCachedPageChunkV2` com um cursor paginado e um user-agent configurado como `curl`. Além disso, é importante buscar os filhos de toggles utilizando a função `syncRecordValuesMain`.

## Próximos passos
- Implementar a chamada à API `loadCachedPageChunkV2`.
- Adicionar suporte para paginação.
- Configurar o user-agent como `curl`.
- Desenvolver a lógica para buscar filhos de toggles.

## Conexões
- [[Design de Interface com Agente]]
