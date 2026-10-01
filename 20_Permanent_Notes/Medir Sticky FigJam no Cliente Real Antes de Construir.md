---
title: Medir Sticky FigJam no Cliente Real Antes de Construir
type: pattern
tags: [figjam, sticky, medicao, cdp, use_figma, workflow, pm-canvas]
created: 2026-10-01
provenance: residencia_cariri_projects
---

# Medir Sticky FigJam no Cliente Real Antes de Construir

O mesmo texto (Inter Medium 40) mede diferente no navegador e no runtime do MCP:

- No navegador o sticky mostra o nome do autor (+16 px de altura): use `sticky.authorVisible = false`.
- Padding difere: 3 linhas = 240 px no navegador vs 244 no MCP; 4 linhas 280 vs 304.
- Cabem só ~10 letras por linha num sticky de 240 de largura a fonte 40 (útil ~205 px;
  "Dashboard" = 209 px quebra, "24/09/2026" quebra).

**Não fixe limiares de altura.** Meça em runtime um sticky-sonda de 3 linhas e derive os
limites (padrão do `measure.mjs`: criar sticky temporário, setar texto, ler altura, remover).

## Fluxo que funcionou (pôsteres PM Canvas)

1. Uma fonte única por pôster em `*.stickies.md`.
2. Conversor gera a entrada do script; medir no navegador até 0 problemas.
3. Build; gravar os links de volta no markdown a partir do retorno do build (`write-links.py`).
4. Subagentes por empresa corrigem stickies em paralelo; builds rodam em série numa aba só.

Ver [[Figma Plugin API via CDP no Chrome Logado - Contorna Cota do MCP]],
[[Reconstruir Template FigJam via use_figma a partir de Medidas de Print]].
