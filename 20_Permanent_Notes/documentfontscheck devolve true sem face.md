---
title: "document.fonts.check devolve true sem face"
type: permanent
created: 2026-11-10T15:00:33
moc: "Design de Interface com Agente"
tags: [javascript, fonts, web]
source_inbox: "03aef56f-document-fonts-check-devolve-true-sem-face.md"
tier: "L2"
score: 0.705
---

# document.fonts.check devolve true sem face

document.fonts.check('16px "X"') devolve true quando nenhuma @font-face casa a família. Para provar fonte carregada, exija FontFace com status loaded e largura medida diferente do fallback.

# document.fonts.check devolve true sem face

## Contexto
O método `document.fonts.check` é usado para verificar se uma fonte está disponível no navegador. No entanto, ele pode retornar `true` mesmo quando nenhuma `@font-face` corresponde à família de fontes especificada.

## Detalhes
Quando chamado com uma fonte que não existe (por exemplo, `document.fonts.check('16px "X"')`), o método retorna `true`. Isso ocorre porque o navegador verifica apenas a existência da fonte e não sua disponibilidade para renderização.

Para provar que uma fonte foi carregada corretamente, é necessário verificar o status do `FontFace` e comparar a largura medida com a largura do fallback. Se a largura medida for diferente da largura do fallback, pode-se concluir que a fonte foi carregada com sucesso.

## Próximos passos
1. Verificar o status do `FontFace` usando `fontFace.status`.
2. Medir a largura da fonte usando `getComputedStyle(element).getPropertyValue('width')`.
3. Comparar a largura medida com a largura do fallback para confirmar a carregamento da fonte.

## Conexões
- [[Design de Interface com Agente]]
