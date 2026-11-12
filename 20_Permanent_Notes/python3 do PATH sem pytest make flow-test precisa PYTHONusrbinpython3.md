---
title: "python3 do PATH sem pytest: make flow-test precisa PYTHON=/usr/bin/python3"
type: permanent
created: 2026-11-10T14:44:57
moc: "Design de Interface com Agente"
tags: [python, pytest, makefile, harness2]
source_inbox: "8d0c81fb-python3-do-path-sem-pytest-make-flow-test-precisa-python-usr.md"
tier: "L2"
score: 0.737
---

# python3 do PATH sem pytest: make flow-test precisa PYTHON=/usr/bin/python3

No dotfiles o python3 do PATH é o venv do harness2, sem pytest. O Makefile de agents/flows usa PYTHON ?= python3. Passe PYTHON=/usr/bin/python3 ou corrija o default.

# python3 do PATH sem pytest: make flow-test precisa PYTHON=/usr/bin/python3

## Contexto
No dotfiles, o python3 do PATH é configurado para o venv do harness2, mas sem pytest. O Makefile de agents/flows usa a variável `PYTHON` com um valor padrão de `python3`.

## Detalhes
O problema ocorre porque o Makefile de agents/flows espera que `PYTHON` seja definido como `/usr/bin/python3`, mas no ambiente atual, ele está sendo definido pelo venv do harness2.

## Próximos passos
- Corrigir a variável `PYTHON` no Makefile para que ela sempre use `/usr/bin/python3`.
- Verificar se há outras partes do código que dependem da variável `PYTHON` e ajustar conforme necessário.

## Conexões
- [[Design de Interface com Agente]]
