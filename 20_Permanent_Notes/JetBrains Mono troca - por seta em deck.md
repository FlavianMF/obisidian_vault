---
title: "JetBrains Mono troca <- por seta em deck"
type: permanent
created: 2026-11-10T14:58:43
moc: "Design de Interface com Agente"
tags: [code, font, timezone]
source_inbox: "0fe86e63-jetbrains-mono-troca-por-seta-em-deck.md"
tier: "L2"
score: 0.769
---

# JetBrains Mono troca <- por seta em deck

Em slide com código, a ligadura da JetBrains Mono desenha '<-' como seta (ex.: TZ=\"<-03>3\" vira ←03>3). Use font-variant-ligatures: none em código e strings POSIX TZ.

# JetBrains Mono troca <- por seta em deck

## Contexto
Em slides com código, a ligadura da JetBrains Mono desenha '<-' como seta, o que pode causar confusão.

## Detalhes
- **Problema**: A fonte JetBrains Mono interpreta '<-' como uma seta.
- **Exemplo**: `TZ=\"<-03>3\"` é exibido como ←03>3.
- **Solução**: Use `font-variant-ligatures: none` em código e strings POSIX TZ para evitar a ligadura.

## Próximos passos
- Verificar se a solução funciona em todos os casos.
- Atualizar o estilo CSS do projeto `.deck-engine-autobuild`.

## Conexões
- [[Design de Interface com Agente]]
