---
title: Skill: Fluxo de Trabalho de Feature Branch
type: pattern
tags: [agentic-ai, git, workflow, automation]
created: 2026-05-21
provenance: manual
---

# Skill: Fluxo de Trabalho de Feature Branch

Esta skill define o comportamento autônomo para gestão de código e versionamento durante o desenvolvimento de novas funcionalidades.

## 🤖 Comportamento Esperado
Sempre que uma nova tarefa ou funcionalidade for solicitada, o agente deve:

1.  **Criação de Branch**: Criar uma branch dedicada com o padrão `feat/nome-da-feature` ou `fix/nome-do-bug`.
    - Comando: `git checkout -b feat/sua-feature`
2.  **Commits de Processo**: Realizar commits incrementais a cada sub-etapa concluída (ex: "define schemas", "impl logic", "add tests").
    - Padrão: [[caveman-commit|Conventional Commits Terse]].
3.  **Finalização**: Não realizar merge automático no `main`. O agente deve deixar a branch pronta e informar ao usuário.

## 🔗 Conexões
- [[Engenharia de Sistemas Agêntica]]
- [[00_META/Agent-Instruction]]
