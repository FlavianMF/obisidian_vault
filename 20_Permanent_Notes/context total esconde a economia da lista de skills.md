---
title: "/context total esconde a economia da lista de skills"
type: permanent
created: 2026-11-10T14:57:46
moc: "Design de Interface com Agente"
tags: [skills-auto-router, economia, API]
source_inbox: "f5bf1c30-context-total-esconde-a-economia-da-lista-de-skills.md"
tier: "L2"
score: 0.756
---

# /context total esconde a economia da lista de skills

Ao reduzir a lista de skills, a linha Skills do /context cai, mas System tools sobe o mesmo valor e o total fica igual. O uso real da API caiu 7,7k. Meça a economia pelo usage da primeira chamada, não pelo /context.

# /context total esconde a economia da lista de skills

## Contexto
Ao reduzir a lista de skills (skillListingBudgetFraction ou skillOverrides), a linha Skills do /context cai, mas System tools sobe o mesmo valor e o total fica igual. Isso pode levar a uma percepção errada de economia.

## Detalhes
O uso real da API caiu 7,7k. A economia deve ser medida pelo uso da primeira chamada, não pelo /context.

## Próximos passos
- Verificar a medida correta do uso da API.
- Atualizar a documentação para refletir a correção.

## Conexões
- [[Design de Interface com Agente]]
