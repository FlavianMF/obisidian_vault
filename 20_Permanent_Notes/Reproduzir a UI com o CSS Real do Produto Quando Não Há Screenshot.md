---
title: Reproduzir a UI com o CSS Real do Produto Quando Não Há Screenshot
type: pattern
tags: [presentation, ui, css, honesty, documentation, demo]
created: 2026-09-11
provenance: projetos_ita
project: projetos_ita
---

# Reproduzir a UI com o CSS Real do Produto Quando Não Há Screenshot

## Contexto

Um deck de produto precisava mostrar a interface de um plugin, e uma busca completa
no disco confirmou: **nenhum screenshot, GIF ou vídeo existia** em todo o projeto.
Só o código.

Mas o plugin renderiza o chat num `Browser` SWT — ou seja, a UI real é HTML/CSS/JS
versionado: `web/css/chat.css` com os tokens exatos (`--accent:#cc785c`,
`--bg:#101012`), e `web/js/chat.js` construindo cada bolha via `document.createElement`.

Em vez de desenhar um mockup, o deck **reconstruiu o DOM estaticamente e importou os
valores verbatim da folha de estilo do produto**, preenchendo com conteúdo de uma
sessão real exportada (latências verdadeiras: 20,4 s, 18,2 s, 44,7 s). Custo: ~25 KB
de CSS inline, contra megabytes de base64 que um screenshot custaria — e resultado
visualmente indistinguível.

## Padrão

Quando a UI é web (Electron, SWT Browser, webview, qualquer front-end), a folha de
estilo publicada **é** o material de referência mais fiel disponível. Reproduzir com
ela é melhor que mockup sintético em três eixos: fidelidade de cor e espaçamento,
custo em bytes, e capacidade de editar o conteúdo mostrado.

Duas regras que acompanham:

1. **Rotular como reprodução, sempre.** Legenda explícita: "interface real do plugin,
   com conteúdo de uma sessão real exportada". Nunca deixar o leitor concluir que é
   captura de tela.
2. **Screenshot real supera a reprodução.** Quando os prints chegaram, todas as
   reproduções saíram do deck — junto com a animação de replay que tinha sido
   construída para substituir o GIF inexistente. Reprodução é ponte, não destino.

Na mesma linha, para "mostrar o agente trabalhando" sem GIF: uma animação CSS/JS
reproduzindo a sequência real (com os tempos verdadeiros exibidos e aviso de que a
animação roda acelerada) funciona — mas foi a primeira coisa descartada quando
apareceu o print de verdade.

## Quando aplicar

Deck, landing ou documentação que precisa mostrar uma interface antes de haver
captura. Vale principalmente quando quem monta o material tem acesso ao código mas
não consegue rodar a aplicação (sem display, sem licença, sem o ambiente).

Antes de montar: **pedir os prints**. Uma shot list específica (o que enquadrar, qual
tema, qual resolução, como provocar o estado desejado na UI) costuma render mais que
qualquer reprodução — o usuário tirou 6 dos 8 pedidos em poucos minutos.

## 🔗 Conexões
- [[Página com Screenshots de Um Tema Não Deve Suportar o Tema Oposto]]
- [[Screenshot de UI Comprime Melhor com Quantização de Cores que com JPEG]]
