---
title: Deck HTML Precisa Escalonar por Altura de Viewport, Não Só por Largura
type: pattern
tags: [css, frontend, responsive, presentation, artifact, layout]
created: 2026-09-11
provenance: projetos_ita
project: projetos_ita
---

# Deck HTML Precisa Escalonar por Altura de Viewport, Não Só por Largura

## Contexto

Um deck de slides em HTML (scroll-snap, um `<section>` por slide com
`min-height:100vh`) recebeu screenshots reais. O CSS das imagens era o padrão
responsivo de sempre:

```css
.shot img{ width:100%; height:auto; }
```

Todos os media queries do arquivo eram por **largura** (`max-width:900px`). Resultado:
o print do hero (1500×844) ocupava os 1240 px do container e renderizava com ~698 px
de altura; somado a título, chips, moldura e legenda, o slide passava de 1100 px
contra ~950 px úteis numa janela Full HD. O usuário reportou: "as imagens estão
grandes, o conteúdo não cabe na tela".

Responsividade por largura é reflexo automático; slide é o caso em que a **altura** é
a dimensão que manda.

## Padrão

Três mecanismos, juntos:

**1. Teto de altura na imagem, em `vh`** — e a moldura encolhendo junto, senão sobram
faixas vazias nas laterais quando a imagem diminui:

```css
.shot{ width:fit-content; max-width:100%; margin-inline:auto; }
.shot img{ width:auto; max-width:100%; height:auto; max-height:46vh; }
```

**2. Media queries por altura**, escalonando tipografia, padding e o próprio teto:

```css
@media (max-height:900px){ .shot img{max-height:42vh} .slide-title{font-size:clamp(24px,2.9vw,36px)} /* … */ }
@media (max-height:760px){ .shot img{max-height:36vh} .slide{padding-block:16px} /* … */ }
```

**3. `justify-content:safe center` como rede de segurança:**

```css
.slide{ justify-content:center; justify-content:safe center; overflow-y:auto; }
```

Com `center` puro, um slide mais alto que a janela corta o topo de forma
**inalcançável** — o conteúdo transborda para cima e não há como rolar até ele.
`safe center` alinha ao início quando não cabe. A declaração dupla dá fallback em
navegador que não conhece a palavra-chave.

## Quando aplicar

Qualquer layout onde um bloco deve caber numa tela inteira sem rolagem interna:
decks de slides, telas de onboarding, hero sections com `100vh`, dashboards em
modo quiosque.

Ao terminar, vale somar as alturas dos slides mais densos à mão (padding + título +
cada bloco) contra a altura útil alvo — sem navegador headless disponível, essa conta
é a única verificação possível antes de publicar.

## 🔗 Conexões
- [[Página com Screenshots de Um Tema Não Deve Suportar o Tema Oposto]]
- [[Screenshot de UI Comprime Melhor com Quantização de Cores que com JPEG]]
