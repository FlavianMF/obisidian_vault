---
title: Figma Plugin API via CDP no Chrome Logado - Contorna Cota do MCP
type: pattern
tags: [figma, figjam, cdp, use_figma, mcp, quota, plugin-api, chrome]
created: 2026-10-01
provenance: residencia_cariri_projects
---

# Figma Plugin API via CDP no Chrome Logado - Contorna Cota do MCP

No plano Starter/Free a cota do MCP `use_figma` acaba em poucas chamadas ("You've reached
the Figma MCP tool call limit on the Starter plan"). Uma aba web do Figma/FigJam logada
expõe a Plugin API no console como o global `figma`, depois que o arquivo carrega.

## Receita

1. Espere `typeof figma === 'object'` na aba (poll via `Runtime.evaluate`).
2. Qualquer script de `use_figma` (top-level await/return) roda igual: embrulhe em
   `(async () => { ...código... })()` e chame CDP `Runtime.evaluate` com
   `awaitPromise: true, returnByValue: true`. Sem cota, reexecuções ilimitadas; leituras
   (`findAllWithCriteria`, alturas de nó) funcionam também.
3. Board novo: abra `https://www.figma.com/board/new` (CDP `PUT /json/new?<url>`) e pegue
   a fileKey da URL resultante. Cai nos rascunhos ("Free") do usuário.
4. `figma.root.name = ...` **não persiste**. Renomeie pela UI: duplo clique no título
   (`Input.dispatchMouseEvent` em ~(96,36)), Ctrl+A, `Input.insertText`, Enter.

## Armadilhas

- Aba em segundo plano é estrangulada pelo Chrome: um build que leva ~1 min levou 5+.
  Chame `Page.bringToFront` antes de avaliar.
- Com 7 GB de RAM e 2 CPUs, mantenha **uma** aba e navegue entre boards (`Page.navigate`).
- Loop "renomear antigo para (v1)" deve checar antes se o board tem seções-pôster ou
  seções de bloco soltas (renomeou 13 blocos soltos de um board; foi revertido).

Ver [[Chrome Headed sem Display - Xvfb + x11vnc + CDP]],
[[Medir Sticky FigJam no Cliente Real Antes de Construir]],
[[Print de Board Figma Logado via Chrome WSLg + CDP]].
