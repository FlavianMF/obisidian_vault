---
title: Reconstruir Template FigJam via use_figma a partir de Medidas de Print
type: pattern
tags: [figma, figjam, use_figma, mcp, template, project-model-canvas, cdp]
created: 2026-09-28
provenance: residencia_00
---

# Reconstruir Template FigJam via use_figma a partir de Medidas de Print

Serve quando é preciso replicar o layout de um template FigJam, como um canvas com
blocos coloridos, sem poder **ler** o template pelo MCP (sem `get_figjam` ou
`get_screenshot`) e sem usar "Duplicate". A solução é medir pelo print e
reconstruir com `use_figma`.

## Receita

1. **Print** do template no zoom "fit" pelo Chrome logado, usando CDP. Ver
   [[Print de Board Figma Logado via Chrome WSLg + CDP]].
2. **Medir em px de tela** com um decodificador PNG em Python stdlib. Varra as
   transições de cor numa linha e numa coluna. Cada borda é 1 px de cor diferente,
   o que dá o bbox e o hex exatos do fundo, da borda e da tag de cada bloco. Anote
   tudo relativo ao canto do pôster.
3. **Escolher um fator único `S`**, em unidades de canvas por px de tela. A regra
   é o **conteúdo fixo mais apertado**. No FigJam o STICKY é 240×240 fixo, então
   `S` sai do bloco que precisa caber mais stickies: 11 em Requisitos deu
   `S = 7.2`. Blocos, fontes e bordas vão todos multiplicados por `S`, e a
   proporção da grade se mantém.
4. **Mapear para nós FigJam:**
   - Pôster: `Section` com fundo branco. O nome da section é só navegação.
   - Bloco: `ShapeWithText` do tipo `ROUNDED_RECTANGLE`, sem texto, com
     `fills`/`strokes` amostrados. Dê ao nó o **nome do rótulo**, que vira a
     chave para achar o bloco nos scripts seguintes.
   - Tag: outro `ShapeWithText` com texto.
   - Títulos e subtítulos: `Text` em Inter.
5. **Stickies em dois passes:**
   - Primeiro crie todos e ponha o texto.
   - Depois posicione em grid com a altura real de cada um.
   - Fonte: a maior que mantém `height == 240`, unificada pelo mínimo dentro de
     cada bloco.
   - Devolva `overflow` no retorno. Se vier vazio, não precisa de chamada de
     verificação.
6. **Cota do MCP no plano Free:** 1 chamada `use_figma` por pôster, ou uma para
   todos. Para conferir, use print pelo Chrome, que não gasta cota.

## Por que funciona

O template é geometria simples: retângulos, pílulas e texto. Pelo print sai tudo
o que importa. A fidelidade de cor vem da amostra de pixel, não de chute na
paleta. O bloco com nome estável permite um segundo script (`fill-stickies`)
preencher pôsteres já criados sem ler o arquivo.

Implementação de referência: repositório da residência PNAAT Cariri,
`_tools/figjam-pm-canvas/` (`build-poster.js`, `fill-stickies.js`, `cdp/`).

Relacionado: [[Project Model Canvas vs ARCADIA - Mapeamento]].
