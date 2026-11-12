---
title: "Regra de estado com CASE por tipo: teste os dois sentidos de cada ramo"
type: permanent
created: 2026-11-10T14:32:36
moc: "Design de Interface com Agente"
tags: [account_state_of, needs_reaccept, privacidade, suíte, laço]
source_inbox: "627c9cd0-regra-de-estado-com-case-por-tipo-teste-os-dois-sentidos-de.md"
tier: "L1"
score: 0.706
---

# Regra de estado com CASE por tipo: teste os dois sentidos de cada ramo

Em account_state_of (needs_reaccept), o ramo de privacidade só tinha teste negativo (marca needs_reaccept) e nenhum positivo (aceita e vira active). Trocar o campo no CASE sobrevive à suíte e prende o usuário num laço de novo aceite. Para toda regra por tipo, teste o aceite que resolve o estado em cada ramo.

# Regra de estado com CASE por tipo: teste os dois sentidos de cada ramo

## Contexto
Em account_state_of (needs_reaccept), o ramo de privacidade só tinha teste negativo (marca needs_reaccept) e nenhum positivo (aceita e vira active). Trocar o campo no CASE sobrevive à suíte e prende o usuário num laço de novo aceite.

## Detalhes
Para toda regra por tipo, é necessário testar o aceite que resolve o estado em cada ramo. Isso garante que a regra funcione corretamente em ambas as direções (aceitar e rejeitar) e evita laços infinitos ou comportamentos inesperados.

## Próximos passos
- Implementar testes para garantir que o aceite resolve o estado em cada ramo.
- Revisar a regra de privacidade para incluir um teste positivo.
- Testar a regra modificada em ambas as direções para verificar se o problema foi resolvido.

## Conexões
- [[Design de Interface com Agente]]
