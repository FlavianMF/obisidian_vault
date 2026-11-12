---
title: "Validador que exige arquivo em disco quebra fixtures: crie stubs no fixture"
type: permanent
created: 2026-11-10T14:52:17
moc: "Design de Interface com Agente"
tags: [agent, flows, validation]
source_inbox: "4bbc5ad8-validador-que-exige-arquivo-em-disco-quebra-fixtures-crie-st.md"
tier: "L1"
score: 0.753
---

# Validador que exige arquivo em disco quebra fixtures: crie stubs no fixture

Ao fazer check_flow exigir que node.prompt exista, as fixtures com prompts fictícios quebraram. Solução: write_flow do conftest cria arquivo vazio por prompt (com guarda para YAML inválido de propósito) e o teste do caso ausente remove o arquivo depois de carregar com validate=False.

# Validador que exige arquivo em disco quebra fixtures: crie stubs no fixture

## Contexto
Ao fazer check_flow exigir que node.prompt exista, as fixtures com prompts fictícios quebraram. 

## Detalhes
A solução proposta é criar stubs no fixture utilizando a função `write_flow` do `conftest`. Essa função cria um arquivo vazio para o prompt, com uma guarda para YAML inválido de propósito. O teste do caso ausente então remove o arquivo depois de carregar com `validate=False`.

## Próximos passos
- Implementar a função `write_flow` no `conftest`.
- Adicionar testes para garantir que o arquivo é criado corretamente e removido após o uso.
- Atualizar os testes existentes para usar a nova implementação.

## Conexões
- [[Design de Interface com Agente]]
