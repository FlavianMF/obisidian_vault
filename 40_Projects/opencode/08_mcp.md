---
title: MCP (Model Context Protocol)
type: project
tags: [opencode, mcp, protocol]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

> Ver [[opencode]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# MCP (Model Context Protocol)

[← Índice](00_indice.md)

Docs: [opencode.ai/docs/mcp-servers](https://opencode.ai/docs/mcp-servers/) · Fonte: `packages/opencode/src/mcp/{index,auth,browser,catalog,oauth-callback,oauth-provider}.ts`, `packages/opencode/src/cli/cmd/mcp.ts`

opencode é um **cliente MCP completo**, construído sobre o package oficial `@modelcontextprotocol/sdk` (confirmado em `mcp.ts`: importa `Client`, `StreamableHTTPClientTransport`, `UnauthorizedError` de `@modelcontextprotocol/sdk/client/*`).

## Configuração

Sob `opencode.jsonc` → `"mcp"`:

```json
{
  "mcp": {
    "local-server": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-everything"],
      "environment": {},
      "cwd": "...",
      "timeout": 5000,
      "enabled": true
    },
    "remote-server": {
      "type": "remote",
      "url": "https://my-mcp-server.com",
      "headers": {},
      "oauth": {
        "clientId": "{env:CLIENT_ID}",
        "clientSecret": "{env:CLIENT_SECRET}",
        "scope": "tools:read"
      }
    }
  }
}
```

- Servidor remoto: OAuth automático (401 dispara Dynamic Client Registration, RFC 7591); fluxo manual via `opencode mcp auth <server-name>`; `"oauth": false` desabilita OAuth (servidores baseados em API key).
- Tools de servidores MCP aparecem ao lado das built-ins; podem ser habilitadas/desabilitadas por agente via padrão glob (ex.: `"mymcp_*": "deny"` na permission de um agente).
- Aviso da própria doc: descrições de tool MCP consomem contexto — ser seletivo em quais servidores/tools habilitar.

## Integração com sistema de tools

`tools.ts` (ver [03_agent_loop.md](03_agent_loop.md)) sintetiza automaticamente três tools de acesso a recurso MCP: `list_mcp_resources`, `list_mcp_resource_templates`, `read_mcp_resource` — além de adaptar as definições de tool nativas de cada servidor MCP para o formato de schema esperado pelo modelo.

## Ver também

- [06_sistema_tools.md](06_sistema_tools.md) — como tools MCP se encaixam ao lado de built-ins
- [07_permissoes_seguranca.md](07_permissoes_seguranca.md) — controle de acesso por padrão glob para tools MCP
- [12_headless_sdk_api.md](12_headless_sdk_api.md) — rotas REST de gerenciamento de MCP (`GET/POST /mcp`, `POST /mcp/{name}/connect`, `/auth`, `/auth/callback`)
