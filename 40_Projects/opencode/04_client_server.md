---
title: Client/server
type: project
tags: [opencode, architecture, client-server, sse, http]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

> Ver [[opencode]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Client/server

[← Índice](00_indice.md)

opencode tem arquitetura client/server explícita — mais nuançada que um servidor sempre-remoto fixo.

## API HTTP REST + SSE + WebSocket

Definida em `packages/opencode/src/server/routes/instance/httpapi/`. `public.ts` exporta `PublicApi`, a superfície pública anotada com OpenAPI.

**Endpoints SSE confirmados** (servidos como `text/event-stream`):
- `GET /event` (schema `Event`)
- `GET /global/event` (schema `GlobalEvent`)
- `GET /api/event` (schema `V2Event`)

**Endpoints REST padrão** (amostra): `GET /session`, `GET /session/{sessionID}/message`, `GET /find/file`, `GET /vcs/diff`, `POST /experimental/workspace`.

Rotas organizadas em ~20 pares `groups/*.ts` + `handlers/*.ts`: `session.ts`, `event.ts`, `provider.ts`, `config.ts`, `file.ts`, `permission.ts`, `mcp.ts`, `project.ts`, `pty.ts`, `tui.ts`, `sync.ts`, `workspace.ts`, `question.ts`, `control-plane.ts`, `control.ts`, `global.ts`, `instance.ts`, `metadata.ts`, `query.ts`, `experimental.ts`.

**WebSocket** também existe (`websocket-tracker.ts` no mesmo diretório `httpapi/`), provavelmente para passthrough de PTY (há rota `pty.ts` e `pty-environment.ts`) e possivelmente sync bidirecional de TUI.

**Framework:** **Effect's `HttpRouter`/`HttpApi`** (Effect-TS), não Hono/Express — `HttpRouter.serve(HttpApiApp.createRoutes(opts))`, com `OpenApi.fromApi(PublicApi)` gerando o schema OpenAPI, e um handler compatível com `fetch` puro exportado para embedding.

**mDNS discovery** (`mdns.ts` em `packages/opencode/src/server/`) disponível para descoberta de serviço em LAN quando o servidor roda não-loopback — suportando controle remoto/multi-dispositivo de uma instância opencode em execução.

**Bus de eventos interno:** `packages/opencode/src/bus/global.ts` implementa `GlobalBus` sobre `EventEmitter` do Node, auto-atribuindo IDs aos eventos publicados; esse é o fan-out de backend que os endpoints SSE assinam e transmitem para downstream.

## Como a TUI realmente se conecta

Achado mais interessante da pesquisa: a TUI **não** sempre fala HTTP de verdade. Fonte: `packages/opencode/src/cli/cmd/tui.ts`.

- O comando cria um **Worker** em background (`new Worker(file, {...})`) rodando a lógica real de servidor/sessão, e estabelece um **cliente RPC** para ele.
- Se o usuário não pediu networking externo (sem `--port`/`--hostname`/`network.mdns`), a TUI fala com o worker via **RPC in-process** com um shim custom de `fetch` e um shim de event-source — evitando overhead real de HTTP/socket para o caso comum de uma máquina só.
- Se networking externo é pedido, o worker recebe instrução de `start` um servidor HTTP real (`client.call("server", network)` retorna uma `url`), e a TUI muda para HTTP genuíno + headers de auth.
- Essa dualidade "embutido-ou-em-rede transparente" é ecoada em `CONTEXT.md`: *"Client Architecture... Embedded OpenCode shares the Effect API through in-memory HTTP transport"* — ou seja, a mesma superfície `PublicApi`/HttpApi é usada seja o transporte in-memory ou um socket real, então o código cliente não precisa saber a diferença.
- `CONTEXT.md` também menciona: "Promise and Effect clients share an SDK Contract IR but maintain independent public type projections" — isso é `packages/client`'s dois entrypoints (`@opencode-ai/client` e `@opencode-ai/client/effect`), gerados diretamente a partir do package do servidor para manter cliente/servidor sincronizados ("prevenir drift de transporte").

## Resumo

Arquiteturalmente é **sempre** um split client/server (TUI é cliente de um servidor de runtime de sessão), mas para uso local single-user de CLI ele colapsa para RPC in-process por performance, mantendo ainda assim a superfície completa exposta via HTTP/SSE/WebSocket real quando se quer acesso remoto, um `opencode serve` headless, a web app, o app desktop Electron, ou clientes de SDK de terceiros anexando.

## Implicação para harness

Essa dualidade é o padrão mais reaproveitável do projeto: definir a API do "servidor" uma única vez (mesmos tipos, mesmo contrato) e trocar só o transporte (in-memory vs. HTTP real) conforme o caso de uso — evita duplicar lógica de cliente entre "modo embutido" e "modo remoto". Ver síntese em [15_implicacoes_harness.md](15_implicacoes_harness.md).
