---
title: "FastAPI Exception handler não evita re-raise no TestClient"
type: permanent
created: 2026-11-10T14:44:31
moc: "Design de Interface com Agente"
tags: [fastapi, exception_handler, testclient]
source_inbox: "1d647861-fastapi-exception-handler-nao-evita-re-raise-no-testclient.md"
tier: "L2"
score: 0.745
---

# FastAPI Exception handler não evita re-raise no TestClient

Handler para Exception no FastAPI roda no ServerErrorMiddleware e o TestClient ainda relança a exceção. Traduza erros do motor em HTTPException dentro da rota (wrapper try/except), não em exception_handler.

# FastAPI Exception handler não evita re-raise no TestClient

## Contexto
No projeto `feat-agent-flows-t5-servidor`, foi identificado um problema com o `TestClient` do FastAPI. O handler de exceção para o FastAPI roda no `ServerErrorMiddleware`, mas o `TestClient` ainda relança a exceção.

## Detalhes
O problema ocorre porque o handler de exceção está sendo chamado pelo middleware, e o `TestClient` não está tratando corretamente a exceção lançada. Para resolver isso, é necessário traduzir os erros do motor em `HTTPException` dentro da rota, usando um wrapper `try/except`.

## Próximos passos
- Implementar um wrapper `try/except` dentro das rotas para capturar e traduzir erros em `HTTPException`.
- Testar a implementação no ambiente de desenvolvimento.
- Atualizar a documentação do projeto com as mudanças realizadas.

## Conexões
- [[Design de Interface com Agente]]
