---
title: "python3 do PATH pode ser venv sem pytest/yaml"
type: permanent
created: 2026-11-10T16:17:45
moc: "Design de Interface com Agente"
tags: [python, virtualenv, pytest, yaml]
source_inbox: "971c2cf0-python3-do-path-pode-ser-venv-sem-pytest-yaml.md"
tier: "L2"
score: 0.757
---

# python3 do PATH pode ser venv sem pytest/yaml

Em worktrees do Traycer o python3 do PATH aponta para o venv do harness2; Makefile deve aceitar PYTHON=/usr/bin/python3 para rodar pytest/PyYAML do sistema.

# python3 do PATH pode ser venv sem pytest/yaml

## Contexto
Em worktrees do Traycer, o python3 do PATH aponta para o venv do harness2. Isso pode causar problemas ao tentar executar pytest ou PyYAML do sistema.

## Detalhes
O Makefile deve aceitar a variável PYTHON=/usr/bin/python3 para garantir que pytest e PyYAML sejam executados do sistema, em vez do venv do harness2.

## Próximos passos
- Atualizar o Makefile para incluir a variável PYTHON=/usr/bin/python3.
- Testar a execução de pytest e PyYAML usando a variável PYTHON definida no Makefile.

## Conexões
- [[Design de Interface com Agente]]
