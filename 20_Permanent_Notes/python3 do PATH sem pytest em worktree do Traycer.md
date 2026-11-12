---
title: "python3 do PATH sem pytest em worktree do Traycer"
type: permanent
created: 2026-11-10T14:05:18
moc: "Design de Interface com Agente"
tags: [python, pytest, traycer, harness2]
source_inbox: "7cd74ba1-python3-do-path-sem-pytest-em-worktree-do-traycer.md"
tier: "L2"
score: 0.733
---

# python3 do PATH sem pytest em worktree do Traycer

No PATH o python3 é o venv do harness2 e não tem pytest. Use /usr/bin/python3 -m pytest e make PYTHON=/usr/bin/python3.

# python3 do PATH sem pytest em worktree do Traycer

## Contexto
No contexto do projeto `feat-agent-flows`, foi identificado um problema onde o Python 3 no PATH é o venv do `harness2` e não contém o `pytest`. Isso resulta em falhas ao executar testes.

## Detalhes
- **Projeto**: `feat-agent-flows`
- **Fonte**: `agent`
- **Contagem**: 1
- **Sessões**: 1
- **IDs de Sessão**: `9c283fb8-ceff-4e10-a9ee-41bd343fb133`

## Próximos Passos
Para resolver este problema, sugere-se o uso do Python 3 instalado globalmente (`/usr/bin/python3`) para executar o `pytest`. Isso pode ser feito de duas maneiras:

1. Usando o comando:
   ```sh
   /usr/bin/python3 -m pytest
   ```

2. Configurando a variável de ambiente `PYTHON` no `make`:
   ```sh
   make PYTHON=/usr/bin/python3
   ```

Essas soluções devem garantir que o `pytest` seja executado corretamente, independentemente do Python 3 configurado no PATH.

## Conexões
- [[Design de Interface com Agente]]
