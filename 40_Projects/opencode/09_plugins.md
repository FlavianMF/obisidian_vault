---
title: Plugins
type: project
tags: [opencode, plugins, hooks, extensibility]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

> Ver [[opencode]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Plugins

[← Índice](00_indice.md)

Docs: [opencode.ai/docs/plugins](https://opencode.ai/docs/plugins/) · Fonte: `packages/plugin/src/index.ts` (npm `@opencode-ai/plugin`, v1.18.29)

**Esse é o artefato mais relevante do projeto inteiro para quem for construir um harness** — permite interceptar/automatizar via código em vez de só config JSON declarativa.

## Onde vivem

- `.opencode/plugins/` (projeto) ou `~/.config/opencode/plugins/` (global) — auto-carregados no startup
- ou npm packages declarados em config:
```json
{ "plugin": ["opencode-helicone-session", "@my-org/custom-plugin"] }
```
(instalados automaticamente via Bun em `~/.cache/opencode/node_modules/`)

## Forma de um plugin

```ts
export type PluginInput = {
  client: ReturnType<typeof createOpencodeClient>
  project: Project
  directory: string
  worktree: string
  experimental_workspace: { register(type: string, adapter: WorkspaceAdapter): void }
  serverUrl: URL
  $: BunShell
}
export type Plugin = (input: PluginInput, options?: PluginOptions) => Promise<Hooks>
```

## Hooks disponíveis (superfície completa)

```ts
interface Hooks {
  dispose?: () => Promise<void>
  event?: (input: { event: Event }) => Promise<void>
  config?: (input: Config) => Promise<void>
  tool?: { [key: string]: ToolDefinition }
  auth?: AuthHook
  provider?: ProviderHook
  "chat.message"?: (input, output: { message: UserMessage; parts: Part[] }) => Promise<void>
  "chat.params"?: (input, output: { temperature; topP; topK; maxOutputTokens; options }) => Promise<void>
  "chat.headers"?: (input, output: { headers: Record<string,string> }) => Promise<void>
  "permission.ask"?: (input: Permission, output: { status: "ask"|"deny"|"allow" }) => Promise<void>
  "command.execute.before"?: (input, output: { parts: Part[] }) => Promise<void>
  "tool.execute.before"?: (input: { tool; sessionID; callID }, output: { args: any }) => Promise<void>
  "tool.execute.after"?: (input, output: { title; output; metadata }) => Promise<void>
  "shell.env"?: (input, output: { env: Record<string,string> }) => Promise<void>
  "tool.definition"?: (input: { toolID: string }, output: { description; parameters: any }) => Promise<void>
  "experimental.chat.messages.transform"?
  "experimental.chat.system.transform"?
  "experimental.provider.small_model"?
  "experimental.session.compacting"?
  "experimental.compaction.autocontinue"?
  "experimental.text.complete"?
}
```

## Por que cada hook importa para um harness

| Hook | Uso para harness |
|---|---|
| `permission.ask` | Substitui/complementa as regras JSON de permission — política de aprovação totalmente programática (ex.: aprovar `bash` só se comando bater com allowlist calculada em runtime) |
| `tool.execute.before` / `.after` | Interceptação/auditoria de toda tool call — log estruturado, replay, rate limiting, redaction de dados sensíveis nos args/output |
| `chat.params` / `chat.headers` | Reescrever a request de LLM saindo (ex.: forçar temperature, injetar header de tracing/tenant) |
| `auth` | Registrar um fluxo de auth de provider inteiro customizado (oauth ou api-key, com prompts próprios) |
| `provider` | Registrar/customizar definição de provider programaticamente |
| `event` | Assinar todos os eventos internos do bus — alternativa in-process ao SSE externo |
| `config` | Reagir/mutar config resolvida antes de aplicada |
| `tool` (registro) | Registrar custom tools dentro do plugin, usando o mesmo helper Zod de [06_sistema_tools.md](06_sistema_tools.md) |

## Registro de custom tool dentro de um plugin

Usa o mesmo helper Zod-based `tool()` de `packages/plugin/src/tool.ts` (ver [06_sistema_tools.md](06_sistema_tools.md)), chaveado sob `Hooks.tool`.

## Ver também

- [07_permissoes_seguranca.md](07_permissoes_seguranca.md) — como `permission.ask` se relaciona com o fluxo request/deferred nativo
- [15_implicacoes_harness.md](15_implicacoes_harness.md) — plugins como ponto de automação preferencial vs. dirigir tudo via API HTTP externa
