---
title: Headless, scriptável, SDK e API — foco harness
type: project
tags: [opencode, headless, sdk, api, ci-cd, harness]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

> Ver [[opencode]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Headless, scriptável, SDK e API — foco harness

[← Índice](00_indice.md)

Esse é o arquivo mais diretamente aplicável ao desenvolvimento de um harness próprio: cobre todos os pontos de entrada não-interativos que o opencode expõe.

## CLI headless

Confirmado direto em `packages/opencode/src/cli/cmd/run.ts` (comentários de fonte e builder de flags):

```
opencode run [message..]
  --command <name>            execução de slash-command
  --continue, -c               continua última sessão
  --session, -s <id>           id de sessão a continuar
  --fork                        fork antes de continuar
  --share                       compartilha a sessão
  --model, -m <provider/model>
  --agent <name>
  --format default|json         "json" = stream de eventos JSON cru, pra parsing por máquina
  --file, -f <path...>          anexa arquivos
  --title <string>
  --attach <url>                anexa a um servidor opencode em execução (sem instância local)
  --password, -p / --username, -u   basic auth pra --attach (default OPENCODE_SERVER_PASSWORD/USERNAME)
  --dir <path>
  --port <number>
  --variant <effort>            esforço de reasoning específico do provider (high/max/minimal)
  --auto                        auto-aprova permissões não negadas ("dangerous!")
  --yolo / --dangerously-skip-permissions   (flags ocultas)
  --interactive, -i              modo interativo split-footer em vez de one-shot
```

Stdin via pipe é concatenado à mensagem (`resolveRunInput`).

**A combinação `--format json` + `--auto`/`--dangerously-skip-permissions` é exatamente o ponto de entrada de CI/automação.** Ver nota de proveniência em [07_permissoes_seguranca.md](07_permissoes_seguranca.md) sobre a flag `--dangerously-skip-permissions`.

## Servidor / API HTTP

Docs: [opencode.ai/docs/server](https://opencode.ai/docs/server/). `opencode serve [--port] [--hostname] [--cors ...]`, porta padrão **4096**, hostname padrão **127.0.0.1**.

Confirmado em `packages/opencode/src/cli/cmd/serve.ts` — o servidor imprime um aviso se `OPENCODE_SERVER_PASSWORD` não estiver setado ("server is unsecured"); auth é **HTTP Basic** via `OPENCODE_SERVER_PASSWORD`/`OPENCODE_SERVER_USERNAME` (usuário padrão `opencode`).

Spec OpenAPI 3.1 gerada e servida em `/doc`; streams SSE em `/event` e `/global/event`.

## Rotas REST relevantes (do `packages/sdk/openapi.json`, 162 paths no total)

- **Ciclo de vida de sessão:** `POST /session`, `GET /session/{id}`, `POST /session/{id}/prompt`, `POST /session/{id}/prompt_async`, `POST /session/{id}/abort`, `POST /session/{id}/fork`, `POST /session/{id}/share` / `DELETE .../share`, `GET /session/{id}/message`, `POST /session/{id}/command`, `POST /session/{id}/revert`, `GET /session/{id}/diff`, `GET /session/{id}/children` (árvore de subagentes)
- **Permissões:** `GET /permission`, `POST /permission/{requestID}/reply`, `GET /session/{id}/permission`, `POST /session/{id}/permissions/{permissionID}`
- **Gestão de MCP:** `GET/POST /mcp`, `POST /mcp/{name}/connect`, `POST /mcp/{name}/auth`, `POST /mcp/{name}/auth/callback`
- **Provider/model/config:** `GET /provider`, `GET /provider/{id}/oauth/authorize`, `GET /config`, `PATCH /config`, `GET /config/providers`

### Namespace v1 vs v2

Existe um **namespace `/api/*` mais novo, em paralelo** (ex.: `/api/session/{id}/prompt`, `/api/session/{id}/wait`, `/api/permission/request`) ao lado dos paths legados sem prefixo — bate com o split `V1`/`v2` do código-fonte (`PermissionV1`, `SessionV1`, `message-v2.ts`, export `./v2` do SDK).

**Para trabalho novo de harness, preferir a superfície `/api/*` + `@opencode-ai/sdk/v2`**, já que claramente é a geração ativamente desenvolvida; os paths sem prefixo/v1 parecem ser a camada legada/compat.

`/experimental/*` expõe gestão de workspace/worktree, sessões em background, movimentação de sessão via control-plane — claramente instável, usar com cautela.

## SDK

npm `@opencode-ai/sdk` (v1.18.29), TypeScript. Dois entrypoints:

```ts
import { createOpencode } from "@opencode-ai/sdk"
const { client } = await createOpencode()              // sobe e gerencia um servidor local

import { createOpencodeClient } from "@opencode-ai/sdk"
const client = createOpencodeClient({ baseUrl: "http://localhost:4096" })  // anexa a servidor existente
```

"Todos os tipos são gerados a partir da spec OpenAPI do servidor."

`@opencode-ai/plugin` (v1.18.29) é um package separado, só para tipos de autoria de plugin/tool, exportando `./tool`, `./tui`, `./v2/effect`.

## ACP (Agent Client Protocol)

Docs: [opencode.ai/docs/acp](https://opencode.ai/docs/acp/). `opencode acp` roda o opencode como subprocesso JSON-RPC-sobre-stdio implementando ACP, para integração de editor (Zed, JetBrains, Avante.nvim, CodeCompanion.nvim). Paridade de feature completa alegada (tools built-in, custom tools, MCP, permissões) exceto `/undo`/`/redo`. Ponto de integração alternativo se a orquestração de um harness falar ACP em vez da API HTTP.

## Não encontrado / não verificado

- SDK oficial em Go: mencionado na nav dos docs (`/docs/go/`) mas conteúdo não inspecionado em profundidade — tratar como "mencionado mas não detalhado", não confirmado.
- SDK oficial em Python: nenhuma evidência encontrada — tratar como não suportado.

## Ver também

- [07_permissoes_seguranca.md](07_permissoes_seguranca.md) — como o fluxo de permission reply se encaixa nessas rotas
- [09_plugins.md](09_plugins.md) — alternativa a dirigir tudo via API externa: automação in-process via hooks
- [15_implicacoes_harness.md](15_implicacoes_harness.md) — recomendação de qual superfície mirar para integração nova
