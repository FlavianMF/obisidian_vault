---
title: "Mutação estreita vence autoteste de regra inteira"
type: permanent
created: 2026-11-10T14:32:25
moc: "Design de Interface com Agente"
tags: [mutação, autoteste, regra, deck-engine]
source_inbox: "978bcb80-mutacao-estreita-vence-autoteste-de-regra-inteira.md"
tier: "L1"
score: 0.776
---

# Mutação estreita vence autoteste de regra inteira

Remover uma regra inteira prova pouco: os testes pegam o caso típico. Mute só um ramo da regra (escape de identidade CSS em vez de hex, URL( maiúsculo, entidade sem ;). No deck-engine sprint 4, 2 de 4 mutações estreitas sobreviveram à suíte de 249 testes.

# Mutação estreita vence autoteste de regra inteira

## Contexto
No deck-engine sprint 4, foi realizada uma mutação estreita em uma regra específica. A intenção era verificar se a remoção total da regra seria suficiente para passar nos testes automatizados.

## Detalhes
- **Regra afetada**: Escape de identidade CSS (em vez de hex, URL( maiúsculo, entidade sem ;).
- **Resultados dos testes**: 2 de 4 mutações estreitas sobreviveram à suíte de 249 testes.

## Próximos passos
- Revisar a eficácia dos testes atuais para garantir que cobrem adequadamente todos os casos.
- Explorar a possibilidade de adicionar mais testes específicos para capturar comportamentos adicionais da regra.

## Conexões
- [[Design de Interface com Agente]]
