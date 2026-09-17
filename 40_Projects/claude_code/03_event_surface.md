---
title: A superfície de eventos do engine
type: project
tags: [claude-code, api-design, event-driven, contract]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# A superfície de eventos

[← Índice](00_indice.md)

Catálogo do contrato publicado em `mods/types/claude-code.d.ts` (10.772 linhas, 432 tipos
exportados, escrito pelo comando `/plugin-types` da versão 2.1.273).

**Contagem exata**, verificável com
`grep -oE "'[a-z]+\.[a-z.]+'" claude-code.d.ts | sort -u | wc -l`:

| Família | Quantos | Onde |
|---|---|---|
| Eventos do engine (`EngineEventOf`) | **34** | `claude-code.d.ts:2846-3202` |
| Chamadas em `$` servidas pelo host (`OpEventOf`) | **50** | `claude-code.d.ts:4478-4744` |
| Total de nomes `substantivo.verbo` | **84** | — |
| Hooks clássicos absorvidos (`classic.<Nome>`) | **33** | `claude-code.d.ts:774, 791` |
| Substantivos em `$` (`CoreEngineInterface`) | **19** | `claude-code.d.ts:1810-2660` |

> **Aviso do próprio arquivo** (`claude-code.d.ts:4`): *EARLY ACCESS — esta superfície pode
> mudar entre releases sem aviso.* Não construir dependência dura sem acompanhar o
> `CHANGELOG` ([17](17_evolucao_changelog.md)).

## Os 19 substantivos de `$`

| Substantivo | Linha | O que cobre |
|---|---|---|
| `plugin` | 1814 | Registro/identidade do próprio plugin |
| `ui` | 1828 | Desenho, painéis, toasts, entrada do usuário |
| `model` | 2004 | Chamada de LLM |
| `audio` | 2058 | Tocar som, falar |
| `mcp` | 2091 | Chamar ferramenta de servidor MCP |
| `session` | 2114 | Estado da sessão: cwd, modelo, mensagens, uso, repo |
| `turn` | 2219 | O turno do modelo |
| `prompt` | 2238 | Montagem do prompt e do contexto |
| `tool` | 2279 | Listar, registrar, descrever, checar e chamar ferramenta |
| `command` | 2332 | Slash commands |
| `config` | 2373 | Configuração exposta ao usuário |
| `agent` | 2403 | Subagentes |
| `fs` | 2430 | Sistema de arquivos |
| `store` | 2486 | Chave-valor persistente do plugin |
| `clock` | 2519 | Tempo: agora, dormir, timer |
| `http` | 2558 | Rede |
| `process` | 2581 | Rodar processo |
| `settings` | 2607 | Ler settings |
| `env` | 2632 | Variáveis de ambiente |

`fs`, `http`, `process`, `env`, `clock` estarem **aqui e não como globais** é o ponto:
é o que torna todo acesso ao mundo externo enganchável, auditável e negável por um hook
acima — ver [02](02_modelo_engine_hooks.md).

## Os 34 eventos do engine

São os pontos onde **o engine avisa** que vai fazer algo. Agrupados por subsistema:

### Loop do agente — 4
| Evento | Fires quando | Retorno de `next(e)` |
|---|---|---|
| `turn.start` | Um turno do modelo começa, antes da primeira chamada de modelo (3174) | `{ turnId }` — só observação |
| `turn.step` | O engine vai mandar uma requisição de modelo, do main ou de um subagente (3183) | a resposta inteira |
| `turn.complete` | O turno terminou (3192) | `{ text }`, a resposta |
| `session.compact` | A conversa vai ser compactada (3140) | `{ messages }` |

### Ferramentas — 3
| Evento | Fires quando | Linha |
|---|---|---|
| `tool.call` | O engine vai rodar uma ferramenta | 2855 |
| `tool.check` | O engine decide se a chamada **pode** rodar | 2867 |
| `tool.describe` | A ferramenta é descrita (para o modelo) | 3034 |

### Prompt e contexto — 6
`prompt.submit` (2974), `prompt.fill` (2986), `prompt.suggest` (2998),
`prompt.section` (3010), `prompt.context` (3022), `skill.prompt` (3093).

### Sessão — 5
`session.start` (3116), `session.receive` (3128), `session.compact` (3140),
`session.attach` (3152), `session.detach` (3157).

### UI — 8
`ui.render` (2876), `ui.resolve` (2885), `ui.press` (2894), `ui.input` (2903),
`ui.select` (2912), `ui.message` (2921), `ui.scroll` (2933), `ui.focus` (2945).

### Agentes — 2
`agent.offer` (2956), `agent.spawn` (2965).

### Comandos e configuração — 4
`command.run` (3046), `command.describe` (3058), `config.set` (3070),
`config.describe` (3082).

### Ciclo de vida e diversos — 3
`plugin.register` (3169), `engine.create` (3201), `attribution.text` (3104).

(`session.compact` aparece em dois grupos acima, por ser ao mesmo tempo um evento de
sessão e um ponto do loop; 4+3+6+5+8+2+4+3 = 35 linhas listadas, 34 eventos distintos.)

## As 50 chamadas em `$`, também eventos

Toda linha abaixo é ao mesmo tempo "um método que o plugin chama" e "um evento que os
hooks acima veem". `e` é o argumento da chamada; o core é a implementação.

| Substantivo | Eventos |
|---|---|
| `model` | `complete`, `classify`, `fork` |
| `session` | `cwd`, `model`, `turns`, `id`, `messages`, `repo`, `surface`, `surfaces`, `authorize`, `usage` |
| `turn` | `abort` |
| `tool` | `list`, `register` |
| `command` | `list`, `register` |
| `config` | `list` |
| `agent` | `list` |
| `mcp` | `call` |
| `audio` | `play`, `speak` |
| `ui` | `toast`, `status`, `log`, `notice`, `invalidate`, `open`, `close`, `blit` |
| `fs` | `read`, `write`, `list`, `exists`, `stat`, `ancestors` |
| `store` | `get`, `set`, `delete`, `keys` |
| `clock` | `now`, `sleep`, `after`, `every` |
| `http` | `fetch` |
| `process` | `run` |
| `settings` | `read` |
| `env` | `get`, `set` |

Nada aqui é privilegiado em relação ao resto: `on("process.run", ...)` intercepta todo
processo que qualquer plugin tentar rodar, igual a `on("tool.call", ...)` intercepta toda
ferramenta.

## Os 33 hooks clássicos, absorvidos

Os hooks JSON de `settings.json` viraram eventos `classic.<Nome>`
(`ClassicEventName`, `claude-code.d.ts:774`; `ClassicHookEvent = HookInput['hook_event_name']`, 791):

| Grupo | Nomes |
|---|---|
| Ferramenta | `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch` |
| Permissão | `PermissionRequest`, `PermissionDenied` |
| Prompt | `UserPromptSubmit`, `UserPromptExpansion`, `InstructionsLoaded`, `MessageDisplay` |
| Sessão | `SessionStart`, `SessionEnd`, `Setup`, `Stop`, `StopFailure`, `Notification` |
| Compactação | `PreCompact`, `PostCompact` |
| Modelo | `PreModelSwitch`, `PostModelSwitch` |
| Subagente / teammate | `SubagentStart`, `SubagentStop`, `TeammateIdle` |
| Tarefa em background | `TaskCreated`, `TaskCompleted` |
| Ambiente | `CwdChanged`, `DirectoryAdded`, `FileChanged`, `ConfigChange` |
| Worktree | `WorktreeCreate`, `WorktreeRemove` |
| MCP | `Elicitation`, `ElicitationResult` |

O resultado deles é normalizado em `ClassicResult` (`claude-code.d.ts:809`), que carrega
tudo que um hook clássico pode responder, cada evento lendo seu subconjunto. Quando vários
hooks de settings respondem o mesmo evento, dobram em um: **última escrita vence, contextos
concatenam** (`claude-code.d.ts:805-807`).

Nomes como `WorktreeCreate`, `TeammateIdle`, `TaskCreated` e `Elicitation` mostram que a
superfície clássica cresceu junto com recursos novos (worktrees, teammates, tasks em
background, elicitation de MCP) — não é uma camada congelada de compatibilidade.

## Como um hook é registrado

```ts
on(pattern, hook)                 // por nome, ou glob, ou negação
on(pattern, matcher, hook)        // + filtro sobre o argumento
```
(`On`, `claude-code.d.ts:4449-4452`.) O `matcher` estreita o tipo de `e` dentro do hook:

```ts
on("tool.check", { tool: "Read" }, () => ({ decision: "allow" }))
```
(exemplo do próprio docstring de `tool.check`, `claude-code.d.ts:2864`).

Hook glob (`on("*")`) recebe `AnyEventHook` (`claude-code.d.ts:328`) e usa
`next.is("tool.call", e)` como type predicate para estreitar, e `next.event` para saber
onde está.

## Eventos de streaming

Alguns eventos são generators em vez de funções: `Chunk`/`ChunkOf`
(`claude-code.d.ts:743-762`) e `StreamingEventName`. `Events[E]` é um mapped type único
justamente para o engine chamar qualquer hook sem cast (TS 4.6, correlated unions —
`claude-code.d.ts:3618-3622`).

## Ver também

- [02](02_modelo_engine_hooks.md) — o modelo por trás desta lista
- [04](04_agent_loop_turn.md) — os eventos de turno em detalhe
- [05](05_sistema_tools.md) — `tool.*` em detalhe
