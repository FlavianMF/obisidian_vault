---
title: "TextField do Flutter: autofillHints padrão é lista vazia, não null"
type: permanent
created: 2026-11-10T15:00:51
moc: "Design de Interface com Agente"
tags: [flutter, dart, onboarding]
source_inbox: "709af14b-textfield-do-flutter-autofillhints-padrao-e-lista-vazia-nao.md"
tier: "L2"
score: 0.755
---

# TextField do Flutter: autofillHints padrão é lista vazia, não null

Para desligar autofill do navegador, passe autofillHints: null explícito. O padrão do TextField é const [], e um teste que exige null falha.

# TextField do Flutter: autofillHints padrão é lista vazia, não null

## Contexto
No projeto `feat-prd2-3-onboarding`, foi identificado um problema relacionado ao uso do `TextField` no Flutter. O comportamento padrão de `autofillHints` é uma lista vazia (`const []`), o que pode levar a problemas em testes que esperam um valor `null`.

## Detalhes
O `TextField` do Flutter não tem um valor padrão para `autofillHints`, e portanto, ele é inicializado como uma lista vazia. Isso pode causar falhas em testes que verificam se `autofillHints` é `null`.

Para desligar o autofill do navegador, é necessário passar explicitamente `autofillHints: null`.

## Próximos passos
- Atualizar os testes para verificar corretamente se `autofillHints` é `null`.
- Documentar o comportamento padrão de `autofillHints` para evitar problemas futuros.
- Considerar implementar uma verificação condicional para lidar com ambos os casos: lista vazia e `null`.

## Conexões
- [[Design de Interface com Agente]]
