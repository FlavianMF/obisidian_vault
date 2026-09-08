---
title: Agent loop — modelo de execução
type: project
tags: [opencode, agent-architecture, llm, tool-use]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

> Ver [[opencode]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Agent loop — modelo de execução

[← Índice](00_indice.md)

Fonte primária: `packages/opencode/src/session/{prompt,processor,tools}.ts`, `packages/opencode/src/tool/tool.ts`, `CONTEXT.md`, `specs/v2/session.md`. Fetches feitos via `raw.githubusercontent.com/.../dev/...` — trechos de código são "como reportado" pelo WebFetch (sumarização, não `cat` byte-exato), mas a estrutura foi corroborada entre múltiplas leituras.

## Visão de conjunto do fluxo

```
prompt do usuário
  → admitido numa "inbox" durável (Session V2: eventos PromptAdmitted/Prompted)
  → SessionRunCoordinator (global de processo, serializa execução por sessão,
    concorrente entre sessões) recolhe o prompt
  → prompt.ts (loop externo) chama processor.ts
  → processor.ts chama llm.stream() (de packages/llm) com system prompt +
    histórico + lista de tools resolvida por tools.ts
  → o stream do LLM emite eventos de texto e/ou tool-call
  → tool calls são executadas via tool.ts's execute(), respeitando
    permission.ts, com plugin hooks disparando antes/depois
  → resultado da tool volta no próximo chunk/turno do stream
  → loop continua até o modelo emitir finish reason que não seja tool-call
    e não haver tool calls pendentes
  → sessão marcada idle
```

## a) `prompt.ts` — loop externo

Loop `while (true)` que processa um passo por iteração:

```ts
while (true) {
  yield* status.set(sessionID, { type: "busy" })
  // ... processa um passo ...
  if (outcome === "break") break
  continue
}
```

Condição de saída: o `finish` da última mensagem do assistente **não** é `"tool-calls"` nem `"unknown"` **e** não há tool calls pendentes para o turno atual do usuário. Tool calls, subtasks e eventos de compaction fazem o loop continuar.

## b) `processor.ts` — interação por passo com o LLM

Processador reativo/streaming, não um if/else explícito de "chamar LLM ou chamar tool":

```ts
const stream = llm.stream(streamInput)
yield* stream.pipe(
  Stream.tap(handleEvent),
  Stream.takeUntil(() => ctx.needsCompaction),
  Stream.runDrain,
)
```

Consome um stream de eventos tagueados vindo do LLM (`text-delta`, `text-end`, `reasoning-start/delta`, `tool-call`, `tool-result`, `step-finish`, 14+ tipos de evento) e despacha para handlers como `ensureToolCall()`/`updateToolCall()`/`completeToolCall()`.

**Implicação-chave:** a execução de tool é dirigida pelas próprias decisões de tool-call do modelo, dentro de um único stream de provider — não é o código do opencode "decidindo" separadamente chamar uma tool. O LLM emite eventos `tool-call` no meio do stream, o opencode executa e devolve `tool-result`.

O processor retorna um de três resultados:
- `"compact"` — overflow de contexto → dispara `compaction.create(...)`
- `"stop"` — negação de permissão ou erro → break
- `"continue"` — repete o loop

## c) `tools.ts` — resolução da lista de tools

Monta a lista de tools passada ao LLM num turno de sessão/agente, a partir de três fontes:

1. `ToolRegistry` built-in filtrado por model/provider/agent/session
2. Recursos expostos por servidores MCP (auto-sintetiza tools `list_mcp_resources`, `list_mcp_resource_templates`, `read_mcp_resource`)
3. Definições de tool de MCP com adaptação de schema

Enforcement de permissão é embutido nesse estágio: o contexto de execução de cada tool carrega uma função `ask`; regras de permissão de nível agent e session são mescladas e checadas contra padrões wildcard (ex.: `mcp:server:*`), com plugin hooks disparando antes/depois da execução para auditoria/mutação. Ver [07_permissoes_seguranca.md](07_permissoes_seguranca.md).

## d) `tool.ts` — abstração de Tool

Um `Def` de tool tem: `id`, `description`, um decoder de `parameters` baseado em schema, `jsonSchema` opcional, um handler `execute(args, ctx) => Effect<ExecuteResult>` e `formatValidationError` opcional. Tools são declaradas via factory `define(id, init)` que constrói o `Def` completo de forma preguiçosa.

Fluxo de execução: decodifica args contra o schema → levanta `InvalidArgumentsError` em falha → roda `execute` → auto-truncamento de output via serviço de truncation → retorna `{title, metadata, output}`.

## e) Tools built-in

Vivem em `packages/opencode/src/tool/`: `read.ts`, `write.ts`, `edit.ts`, `apply_patch.ts`, `glob.ts`, `grep.ts`, `shell.ts` (+ `shell/`), `lsp.ts`, `webfetch.ts`, `websearch.ts` (+ variante `mcp-websearch.ts`), `todo.ts`, `question.ts`, `task.ts` (spawn de subagente), `plan.ts`, `skill.ts`, `code-mode.ts` (tool do sandbox codemode), `external-directory.ts`. Cada uma tem um `.txt` pareado (ex.: `edit.txt`, `read.txt`) — quase certamente o texto de descrição da tool injetado no prompt do modelo. Lista funcional detalhada em [06_sistema_tools.md](06_sistema_tools.md).

## f) `packages/opencode/src/agent/`

`agent.ts` (definição/config de agente — "build" vs "plan" vs subagentes customizados), `subagent-permissions.ts` (escopo de permissão quando um subagente é criado via tool `task`), `prompt/` (templates de prompt de agente). Detalhado em [13_multiagente_subagentes.md](13_multiagente_subagentes.md).

## Gestão de contexto e compaction (Session V2)

Por `CONTEXT.md` e `specs/v2/session.md`, o opencode modela histórico de conversa como **"Context Epochs"** — um contexto de sistema baseline imutável por época, que só muda em fronteiras seguras de turno do provider ("lazy reconciliation": mudanças de contexto são amostradas/admitidas só entre turnos, nunca de forma assíncrona no meio do stream).

Output de tool grande é derramado em arquivos temporários gerenciados, com preview limitado mantido no histórico (`tool-output-store.ts` em `packages/core/src/`). Compaction automática substitui a "representação ativa do modelo" do histórico por um checkpoint oculto, mantendo a transcrição completa durável.

## Para quem for construir um harness

Pontos de intercepção naturais nesse loop, se for orquestrar o opencode via API/plugin (ver [12_headless_sdk_api.md](12_headless_sdk_api.md) e [09_plugins.md](09_plugins.md)):
- Hook de plugin `tool.execute.before`/`.after` — auditoria/mutação de toda tool call, sem precisar reimplementar o loop
- Hook `permission.ask` — política de aprovação programática, substitui/complementa as regras JSON de `permission`
- SSE em `/event`/`/api/event` — observar o stream de eventos do processor de fora, sem embutir o loop
- `GET /session/{id}/children` — navegar árvore de subagentes gerada pela tool `task`
