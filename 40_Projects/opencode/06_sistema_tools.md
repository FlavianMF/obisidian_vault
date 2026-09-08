---
title: Sistema de tools
type: project
tags: [opencode, tool-use, schema, zod]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

> Ver [[opencode]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Sistema de tools

[← Índice](00_indice.md)

Docs: [opencode.ai/docs/tools](https://opencode.ai/docs/tools/) · Fonte: `packages/opencode/src/tool/*.ts`

## Tools built-in

| Tool | Propósito |
|---|---|
| `bash` | Executa comandos de shell |
| `edit` | Edição de arquivo por substituição de string exata |
| `write` | Cria/sobrescreve arquivos (gatekeeping pela permissão `edit`) |
| `read` | Lê conteúdo de arquivo (suporta ranges de linha) |
| `grep` | Busca de conteúdo por regex |
| `glob` | Busca de arquivo por padrão |
| `lsp` | Queries de LSP (definições/referências/hover) — experimental, precisa de `OPENCODE_EXPERIMENTAL_LSP_TOOL=true` |
| `apply_patch` | Edição de arquivo baseada em patch |
| `skill` | Carrega um arquivo `SKILL.md` no contexto |
| `todowrite` | Gestão de lista de todo (desabilitada por padrão para subagentes) |
| `webfetch` | Busca uma URL |
| `websearch` | Busca na web (precisa de provider OpenCode ou `OPENCODE_ENABLE_EXA`/`OPENCODE_ENABLE_PARALLEL`) |
| `question` | Faz uma pergunta de esclarecimento ao usuário no meio da execução |
| `task` | Cria um subagente (ver [13_multiagente_subagentes.md](13_multiagente_subagentes.md)) |

## Dois sistemas de schema — ponto importante para harness

**Tools internas/core** (`packages/opencode/src/tool/tool.ts`) são definidas com **Effect-TS `Schema`**, não Zod:

```ts
Def<Parameters extends Schema.Decoder<unknown>, ...> {
  execute(args, ctx): Effect.Effect<ExecuteResult>
}
```

Tool defs carregam um `jsonSchema?: JSONSchema7` opcional para o que de fato é enviado ao modelo. Falhas de decode de argumento levantam um `InvalidArgumentsError` tipado cuja `.message` é devolvida ao LLM como texto de erro da tool (um empurrão de "reescreva seu input") — relevante se for interceptar/replay de tool calls.

**Tools públicas/de plugin** (`packages/plugin/src/tool.ts`, npm `@opencode-ai/plugin`) usam **Zod**:

```ts
export function tool<Args extends z.ZodRawShape>(input: {
  description: string
  args: Args
  execute(args: z.infer<z.ZodObject<Args>>, context: ToolContext): Promise<ToolResult>
}) { return input }
tool.schema = z
```

`ToolContext` = `{ sessionID, messageID, agent, directory, worktree, abort, metadata(...), ask(...) }`.

## Custom tools

Docs: [opencode.ai/docs/custom-tools](https://opencode.ai/docs/custom-tools/). Arquivo em `.opencode/tools/` (projeto) ou `~/.config/opencode/tools/` (global); nome do arquivo = nome da tool (`database.ts` → tool `database`). Custom tools sobrescrevem built-ins de mesmo nome.

## Ver também

- [07_permissoes_seguranca.md](07_permissoes_seguranca.md) para como a execução de cada tool passa por um gate de permissão
- [09_plugins.md](09_plugins.md) para registrar tool customizada dentro de um plugin (mesmo helper `tool()` baseado em Zod, chaveado sob `Hooks.tool`)
- [03_agent_loop.md](03_agent_loop.md) para como a lista de tools é resolvida e injetada no stream do LLM
