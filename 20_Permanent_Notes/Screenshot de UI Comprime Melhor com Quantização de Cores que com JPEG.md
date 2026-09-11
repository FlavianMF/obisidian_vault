---
title: Screenshot de UI Comprime Melhor com Quantização de Cores que com JPEG
type: pattern
tags: [imagemagick, images, optimization, screenshots, artifact, data-uri]
created: 2026-09-11
provenance: projetos_ita
project: projetos_ita
---

# Screenshot de UI Comprime Melhor com Quantização de Cores que com JPEG

## Contexto

Seis screenshots de um plugin Eclipse precisavam ser embutidos como data URI num
deck HTML (host externo é bloqueado por CSP em Artifacts). O maior era a janela
inteira da IDE: 1917×1079, 286 KB de PNG.

O reflexo — redimensionar o PNG — **aumentou** o arquivo:

| Tratamento | Tamanho |
|---|---|
| Original 1917×1079 | 286 KB |
| `-resize 1500x` (PNG puro) | **381 KB** ⬆ |
| `-resize 1500x -quality 88` (JPEG) | 170 KB, texto pequeno borrado |
| `-resize 1500x -colors 256` (PNG) | **118 KB**, texto nítido |

Os outros cinco prints caíram para 12–24 KB cada com o mesmo tratamento. Total
embutido: 211 KB.

## Padrão

```bash
convert entrada.png -resize 1500x -colors 256 -strip saida.png
```

O porquê: screenshot de interface tem **poucas cores** (fundos chapados, texto de
uma cor, bordas de uma cor) e bordas duras. É o caso ideal para paleta indexada.
JPEG é o oposto — foi feito para gradientes fotográficos e destrói exatamente o que
mais importa num print de UI: a nitidez de letra pequena e de linha de 1 px.

O redimensionamento sozinho inflar o PNG é contraintuitivo mas esperado: a
reamostragem introduz cores intermediárias por antialiasing, explodindo a paleta que
o PNG comprimia bem. `-colors` desfaz esse dano.

Para foto de verdade no mesmo projeto (um A380 de 3008×2000), o caminho continuou
sendo JPEG: `-resize 1600x -quality 78` levou 1,43 MB para 304 KB. Os dois
tratamentos coexistem no mesmo build — **o critério é a natureza da imagem, não o
formato de origem**.

## Quando aplicar

Sempre que screenshot de UI precisar ser embutido (data URI, e-mail, PDF, docs) ou
trafegar. Checar o resultado visualmente uma vez antes de fechar — a 256 cores o
dano é invisível em UI, mas em imagem com gradiente aparece como banding.

## 🔗 Conexões
- [[Substituir Imagem por Placeholder no Template e Injetar Data URI no Build]]
- [[Deck HTML Precisa Escalonar por Altura de Viewport, Não Só por Largura]]
