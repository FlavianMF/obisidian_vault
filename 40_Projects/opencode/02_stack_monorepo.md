---
title: Stack e monorepo
type: project
tags: [opencode, monorepo, typescript, bun, effect-ts]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

> Ver [[opencode]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Stack e monorepo

[← Índice](00_indice.md)

## Tech stack

- **Linguagem:** TypeScript em praticamente todo o monorepo (core, server, TUI, desktop, sistema de plugins). Sem Go/Bubbletea nesta versão — a TUI atual é TS/TSX (diferente de linhagens antigas de "opencode" baseadas em Go que aparecem em buscas — cuidado ao pesquisar, esse é outro projeto).
- **Package manager / runtime:** **Bun** (v1.3.14 fixado no `package.json` raiz; `bunfig.toml` em múltiplos níveis de package).
- **Orquestração de monorepo:** **Turborepo** (`turbo.json`) para cache/orquestração de tasks entre workspaces.
- **Framework de TUI:** **SolidJS + OpenTUI** (`@opentui/core`, `@opentui/solid`, `@opentui/keymap`, `opentui-spinner`) — não é React/Ink nem uma TUI em Go.
- **App desktop:** **Electron** (macOS/Windows/Linux).
- **Framework de backend:** **Effect-TS** (`effect` 4.0.0-beta.83) usado de forma pervasiva para efeitos funcionais, tratamento de erro, e o módulo `HttpRouter`/`HttpApi` do próprio Effect para o servidor — não é Hono/Express.
- **UI web/desktop:** SolidJS (1.9.10), Vite (7.1.4), Tailwind CSS (4.1.11).
- **Banco de dados/ORM:** Drizzle ORM (1.0.0-rc.2) com packages próprios de integração Effect+SQLite (`packages/effect-drizzle-sqlite`, `packages/effect-sqlite-node`) — persistência local/embutida do estado de sessão.
- **SDKs de LLM/dependências:** Vercel AI SDK (`ai`, 6.0.168) + SDK da Anthropic (3.0.111), usados ao lado dos adapters próprios de provider em `packages/llm`.
- **Testes:** Playwright (1.59.1) para e2e/UI; por convenção do `AGENTS.md`, testes rodam por package, evitando mocks quando possível; `bun typecheck` em vez de `tsc` cru.
- **Lint/format:** oxlint; Prettier configurado sem ponto e vírgula e linha de 120 caracteres.
- **Infra/deploy:** arquivos de config **SST** (Serverless Stack) espalhados por quase todo package (deploy do produto hospedado/console); Nix flake para dev shells/empacotamento reprodutível; Docker (`Dockerfile` em `packages/opencode`).
- **Schema/validação:** **Effect Schema** é o mecanismo principal de validação de parâmetros de tool, config e tipos de protocolo internos — não Zod (Zod é usado só na camada pública de plugins, ver [06_sistema_tools.md](06_sistema_tools.md)). Convenção do `AGENTS.md`: "confiar em inferência de tipo; usar helpers de Effect schema para parsing de JSON".

## Layout de topo do repositório

| Path | Propósito |
|---|---|
| `packages/` | O monorepo — ~32 packages, ver tabela abaixo |
| `sdks/` | Contém `packages/sdk` (SDK JS/TS gerado) |
| `infra/` | Infra-as-code de deploy |
| `specs/` | Documentos internos de design/RFC (fonte rica de rationale — ver seção final) |
| `nix/`, `flake.nix` | Empacotamento Nix / dev shell |
| `patches/` | Patches de dependências Bun/npm (23 deps patcheadas) |
| `script/`, `perf/` | Scripts de repositório e testes de performance |
| `.github/`, `.husky/`, `.vscode/` | CI, git hooks, config de editor |
| `AGENTS.md`, `CONTEXT.md`, `CONTRIBUTING.md`, `SECURITY.md`, `STATS.md` | Docs raiz — ver "Documentos de design" abaixo |

## Tabela de packages

| Package | Responsabilidade |
|---|---|
| `packages/opencode` | **Aplicação principal** — entrypoint da CLI, runtime do agente (sessão/tool/agente/provider/servidor), a maior parte da lógica de negócio |
| `packages/core` | Camada de domínio/schema compartilhada: config, credenciais, database, modelo de domínio de sessão (V2), permissões, tipos de plugin, schema de tool, helpers de git/filesystem |
| `packages/llm` | Abstração multi-provider de LLM, **standalone e schema-first** (README/DESIGN.md próprios — ver [05_providers_llm.md](05_providers_llm.md)) |
| `packages/server` | Package de servidor separado e menor (routes/handlers/middleware, `api.ts`, `auth.ts`, `cors.ts`) — parece uma superfície de servidor mais enxuta/antiga ou específica de deploy SST, distinta de `packages/opencode/src/server` |
| `packages/protocol` | Definições de wire-format/protocolo entre `schema` e `server` (por `CONTEXT.md`: "Protocol compõe valores de Schema em wire formats") |
| `packages/schema` | Definições de schema base (camada de valores semânticos) |
| `packages/client` | Clientes HTTP auto-gerados a partir da API do servidor — variante Promise (`@opencode-ai/client`, fetch puro) e variante Effect (`@opencode-ai/client/effect`), geradas lendo o package do servidor diretamente "para prevenir drift de transporte" |
| `packages/sdk` (`sdks/`) | SDK JS + `openapi.json` — superfície pública de SDK, publicada como `@opencode-ai/sdk` |
| `packages/tui` | Terminal UI — TypeScript/TSX, SolidJS + OpenTUI |
| `packages/app` | Componentes de UI web compartilhados (SolidJS) |
| `packages/desktop` | App desktop nativo Electron |
| `packages/web` | App web / site de produto-marketing |
| `packages/console` | Backend do produto SaaS hospedado/enterprise: subpastas `app/`, `core/`, `function/`, `mail/`, `resource/`, `support/` — billing/suporte/notificação, não faz parte do loop local do agente |
| `packages/enterprise`, `packages/identity` | Features enterprise/auth do produto hospedado |
| `packages/plugin` | Fonte do package público `@opencode-ai/plugin` — superfície de API de plugin (ver [09_plugins.md](09_plugins.md)) |
| `packages/codemode` | **Sandbox de execução JS confinado** para agentes — o modelo escreve um pequeno programa JS que só pode chamar as tools fornecidas pelo host, sem acesso a filesystem/processo/rede/módulos além dos bindings explícitos de tool; limites de recurso (timeout, contagem de chamadas, tamanho de output). Tem doc de design própria (`codemode.md`) — é a versão do opencode do padrão "code execution over tools" (cf. Anthropic/Cloudflare "code mode" para MCP) |
| `packages/session-ui` | Componentes de UI relacionados a sessão, compartilhados entre TUI/web/desktop |
| `packages/effect-drizzle-sqlite`, `packages/effect-sqlite-node` | Integração Effect+SQLite/Drizzle — persistência local |
| `packages/http-recorder` | Gravação de tráfego HTTP, provavelmente para testes/replay de chamadas de API de LLM |
| `packages/httpapi-codegen` | Codegen para tipos/clientes da API HTTP |
| `packages/storybook` | Ambiente de dev de componentes/UI |
| `packages/slack`, `packages/function`, `packages/containers`, `packages/stats`, `packages/docs` | Integração Slack, funções serverless, defs de container, geração de stats do GitHub, e fonte do site de docs (Mintlify, `docs.json` + `.mdx`) |

## Nuance estrutural importante

Tanto `packages/core/src/session/` quanto `packages/opencode/src/session/` existem, com nomes de arquivo sobrepostos (ambos têm lógica de compaction/history/prompt/message). Isso sugere fortemente que `packages/core` guarda o modelo de domínio mais novo **"Session V2"** (event-sourced: `context-epoch.ts`, `run-coordinator.ts`, `projector.ts`, `execution/`, `runner/`) enquanto `packages/opencode/src/session` é a camada de runtime operacional (invocação de LLM, resolução de tool, reminders/todo, retry) que compõe em cima dele. Ver [03_agent_loop.md](03_agent_loop.md).

`AGENTS.md` documenta explicitamente uma regra de direção de dependência: **Schema → Core/Protocol → Server; Client depende só de Schema/Protocol.**

## Documentos de design internos (rationale)

Diferente da maioria dos projetos OSS, o repositório é bem documentado internamente via `specs/` e arquivos `DESIGN.md`/`AGENTS.md`/`CONTEXT.md` locais por package, em vez de um único `ARCHITECTURE.md` no topo (não existe um — `CONTEXT.md` cumpre esse papel na raiz):

- **`/CONTEXT.md`** — doc conceitual de arquitetura na raiz. Explica "System Context" (fatos tipados e com fonte, injetados no modelo como "Mid-Conversation System Messages"), "Context Epochs" (baselines imutáveis por época), e o porquê da **lazy reconciliation**: mudanças de contexto só são amostradas/admitidas em fronteiras seguras de turno do provider, nunca de forma assíncrona no meio do turno — evitando mutação não-determinística de contexto. Também documenta semântica "stale-while-revalidate" para fontes de contexto indisponíveis (manter último estado bom em vez de zerar), e o design de tool-output durável (derramar output grande em arquivo temporário, manter preview limitado no histórico).
- **`/AGENTS.md`** — guia de contribuidor/agente na raiz, codificando invariantes arquiteturais: direção estrita de dependência (Schema → Core/Protocol → Server; Client → só Schema/Protocol), a regra "uma chamada `llm.stream()` por turno de provider", design process-local/baseado-em-ID da Session V2 (pendente de clustering futuro), e regras de estilo de código que funcionam como filosofia de design (preferir lógica inline a abstração prematura, early returns em vez de `else`).
- **`specs/project.md`** — spec de hierarquia de recursos REST para o modelo projeto→sessão, desenhado explicitamente para suportar uma instância opencode gerenciando múltiplos projetos/worktrees concorrentemente; o próprio doc sinaliza certos endpoints com escopo de diretório como "estranhos" — tradeoff auto-consciente, não uma fachada polida.
- **`specs/v2/session.md`** — doc de rationale mais substancial encontrado. Explica por que a Session V2 substituiu a V1: separar "registro de prompt" de "execução de prompt" como responsabilidades distintas, para que a admissão durável (uma inbox consultável/replayável) aconteça antes de um prompt se tornar visível ao modelo. Introduz o `SessionRunCoordinator` (serializa execução por sessão, concorrente entre sessões) como prevenção de race conditions maximizando throughput; explica compaction automática como preservação da transcrição completa durável, trocando só a *representação ativa* voltada ao modelo; e explica durabilidade de tool call ("persiste cada tool call local completo de forma durável antes de iniciar avidamente sua execução filha estruturada") como prevenção de efeitos colaterais perdidos em caso de crash.
- **`specs/v2/provider-model.md`** — rationale de aninhar modelos sob providers (colisão de IDs entre providers), o campo `enabled` não-booleano (trilha de auditoria de *por que* um provider está disponível), resolução preguiçosa de endpoint, e a política deliberada de "falhar explicitamente em vez de degradar silenciosamente" para combinações provider/rota não suportadas.
- **`packages/llm/DESIGN.md`** — rationale de separar "protocol" (transformação de wire format) de "route" (endpoint/auth) dentro do package de LLM, habilitando eventos de streaming uniformes entre 10+ APIs de provider heterogêneas.
- **`packages/codemode/codemode.md`** — rationale do padrão "code mode" de JS sandboxed: deixa o modelo agrupar múltiplas tool calls em um programa gerado em vez de uma tool call por round-trip, garantindo que não pode exceder a autoridade já concedida pelo host (sem eval, sem classes, sem acesso ambiente a FS/rede/processo) — um "authority boundary" explícito declarado no doc.
