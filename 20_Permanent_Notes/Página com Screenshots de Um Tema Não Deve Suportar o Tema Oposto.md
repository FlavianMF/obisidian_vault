---
title: Página com Screenshots de Um Tema Não Deve Suportar o Tema Oposto
type: trap
tags: [css, frontend, dark-mode, artifact, presentation, screenshots]
created: 2026-09-11
provenance: projetos_ita
project: projetos_ita
---

# Página com Screenshots de Um Tema Não Deve Suportar o Tema Oposto

## Contexto

Um deck HTML embutia seis screenshots de um plugin Eclipse, todos capturados no
**tema claro**. O CSS seguia a boa prática usual de respeitar a preferência do
leitor:

```css
:root{ /* paleta clara */ }
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){ /* paleta escura */ }
}
:root[data-theme="dark"]{ /* paleta escura */ }
```

O autor considerava o deck "claro" — afinal, o `:root` era claro. O usuário, com o
sistema operacional em dark mode, abriu e viu **tudo escuro**, com os seis prints
claros brilhando como retângulos de luz no meio da página. Reportou duas vezes:
"a apresentação ainda está no tema escuro".

## Armadilha

Duas coisas se combinam:

1. **O bloco escuro vence silenciosamente.** Quem escreve o CSS olha o `:root` e
   conclui "é claro". Mas o media query decide na máquina do leitor, e o autor quase
   sempre testa num ambiente só.
2. **Imagem embutida não tem tema.** Todo o resto da página se adapta; o screenshot
   não. Suportar os dois temas garante que, para metade dos leitores, o conteúdo
   mais importante da página vai destoar do fundo.

## Padrão

Quando a página embute imagens presas a um tema — screenshots de UI, capturas de
IDE, gráficos exportados com fundo fixo — **comprometa-se com um tema só**, o mesmo
das imagens:

```css
html{color-scheme:light;}
:root{ /* paleta completa, explícita */ }
/* nenhum bloco prefers-color-scheme, nenhum [data-theme] */
```

Isso é escolha deliberada, não omissão: a paleta continua inteira e explícita, e o
`body` pinta o próprio fundo a partir de token (página transparente herda o fundo do
host). O que sai é só a *alternância*.

O caminho inverso também vale: se os prints forem escuros, o deck vira escuro.
A regra é o alinhamento, não a cor.

## Quando aplicar

Qualquer artifact, landing, deck ou documentação que embuta screenshot de interface.
Se a página é 100% texto e vetor (SVG com `currentColor`), aí sim suporte os dois
temas normalmente — sem imagem raster presa a um tema, não há conflito.

## 🔗 Conexões
- [[Deck HTML Precisa Escalonar por Altura de Viewport, Não Só por Largura]]
- [[Reproduzir a UI com o CSS Real do Produto Quando Não Há Screenshot]]
