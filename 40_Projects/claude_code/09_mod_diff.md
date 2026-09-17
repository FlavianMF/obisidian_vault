---
title: mods/diff dissecado — um mod real, inteiro
type: project
tags: [claude-code, plugins, typescript, code-reading, facade-pattern]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# `mods/diff` dissecado — um mod real, inteiro

[← Índice](00_indice.md)

779 arquivos, 577 deles `.ts`/`.tsx` sob `hooks/`, 199 sob `tests/`. É o maior artefato de
código real publicado sobre o harness — e o único lugar onde dá para ver como a Anthropic
**escreve** contra a própria API de plugins.

O que ele faz: o comando `/diff`, que abre as mudanças não commitadas da sessão num painel
ao lado da transcrição, arquivo por arquivo com seus hunks, atualizando enquanto o Claude
edita e roda comandos (`mods/diff/.claude-plugin/plugin.json`).

Ele é **built-in** — sai embutido no binário — e o folder é o source do que já está lá.

## O manifesto é minúsculo

```json
// .claude-plugin/plugin.json
{ "name": "diff", "version": "0.1.0", "description": "...", "author": { "name": "Anthropic" } }
```
```json
// hooks/hooks.json
{ "description": "...", "modules": ["./register.ts"] }
```

Um plugin = um manifesto + um `hooks.json` que nomeia módulos + TypeScript. Nada de build
step declarado, nada de dependência: o `hooks.json` aponta direto para `./register.ts`.

## As 10 registrações de hook

Todo o comportamento do painel sai destas dez linhas de `hooks/register.ts`:

| # | Registro | Papel |
|---|---|---|
| 1 | `on('session.start', ...)` | Liga o `Host` e registra o comando `/diff` |
| 2 | `on('ui.render', { component: 'PromptHint' }, ...)` | Lê largura e fullscreen do viewport, de carona |
| 3 | `on('ui.render', { component: 'Pane' }, ...)` | **Desenha o painel** |
| 4 | `on('command.run', { command: 'diff' }, ...)` | Abre/fecha |
| 5 | `on('ui.close', { id: PANE_ID }, ...)` | Intercepta o fechamento |
| 6 | `on('ui.focus', { plugin: PLUGIN_NAME }, ...)` | Segue o anel de foco |
| 7 | `on('ui.scroll', { requestId: PANE_ID }, ...)` | Responde a roda do mouse |
| 8 | `on('command.run', { command: ['clear','resume'] }, ...)` | Reseta estado |
| 9 | `on('tool.call', { tool: [...EDITING, ...SHELL] }, ...)` | Detecta edição e agenda refresh |
| 10 | `on('prompt.submit', ...)` | Injeta os hunks de um arquivo no próximo prompt |

Note que **nove das dez usam matcher**. O matcher não é açúcar: ele estreita o tipo de `e`
dentro do hook e evita que o hook seja chamado para eventos que não interessam.

## O padrão mais importante: a fachada `Host`

Em `session.start`, o mod **não guarda `$`**. Ele constrói um objeto `Host` que fecha sobre
`$`, membro a membro:

```ts
on('session.start', async ($, e, next) => {
  await bind({
    now:       () => $.clock.now(),
    after:     (ms, fn) => $.clock.after(ms, fn),
    run:       (argv, init) => $.process.run(argv, init),
    readFile:  path => $.fs.read(path),
    storeGet:  key => $.store.get(key),
    messages:  () => $.session.messages(),
    openPane:  pane => $.ui.open(pane),
    registerCommand: spec => $.command.register(spec),
    mark:      entry => $.telemetry.mark(entry),
    // ...
  }, e.cwd)
  return next(e)
})
```

E o tipo é documentado exatamente assim (`hooks/host/host.ts`):

> O engine como o `session.start` o ligou a partir do seu `$`, cada membro escrito
> `$.noun.event(...)` ali; usado por todo hook, timer e aperto posterior.

Três ganhos de uma vez:

1. **A superfície de capacidade do mod fica declarada num tipo.** Dá para ler `Host` e saber
   tudo que o `diff` pode fazer no mundo — 19 membros. Nada mais.
2. **Todo o resto do código não conhece o engine.** As 577 funções tomam `Host`, não `$`.
3. **Timers e closures continuam funcionando fora do dispatch.** `$` vive dentro de um hook;
   o timer que dispara 300 ms depois não tem um. O `Host` capturado tem.

Para um harness próprio, este é o padrão a copiar: *não passe o mundo adiante, passe uma
fachada nomeada dele.*

## Estado: closure, não módulo

Tudo que o mod lembra são variáveis locais de `register`: `host`, `backend`, `model`,
`isPaneOpen`, `armed`, `timers`, `bodyLoads`… Nenhuma global. Recarregar o plugin recria a
closure inteira, e `register` roda de novo (`Register`, `claude-code.d.ts:5901`).

O modelo de UI é imutável e substituído por cópia: `model = { ...model, selectedPath: path }`.
Redux sem Redux.

## Como o painel desenha

```ts
on('ui.render', { component: 'Pane' }, async ($, e, next) => {
  if (e.requestId !== Names.PANE_ID || !host || !isOnPaneSurface(e)) return next(e)
  const { Box, Text, Button, Select, Code } = await $.ui.resolve(e)
  ...
  return Views.paneView({ ui: { Box, Text, Button, Select, Code }, ... }, model, ...)
})
```

Os elementos **não são globais**: vêm de `$.ui.resolve(e)`, a tabela da superfície
(terminal, desktop, …). O mesmo código de view desenha em superfícies diferentes porque a
tabela é resolvida por evento. Se o `requestId` não é o do painel dele, o hook devolve
`next(e)` sem tocar em nada — cortesia obrigatória num sistema onde todo hook vê todo render.

## Negar um evento para mudar o significado de uma tecla

O caso mais elegante do arquivo, em `ui.close`:

```ts
const isBack = e.origin.kind === 'person' && model.placement === 'inline'
             && model.dialogView === 'detail'
if (isBack && host) {
  // ...volta para a lista de arquivos...
  return { deny: 'back to the file list' }
}
```

Escape fecharia o painel; o mod **nega o fechamento** e usa o evento para voltar da vista de
detalhe para a lista. `{ deny }` não é só segurança — é redefinição de comportamento.
E note `e.origin.kind === 'person'`: o mod só faz isso quando foi a pessoa que fechou, não
quando outro plugin fechou.

## Observar sem interferir

```ts
on('tool.call', { tool: [...EDITING_TOOLS, ...SHELL_TOOLS] }, async ($, e, next) => {
  let result
  try { result = await next(e); return result }
  finally { if (host) afterTool(host, e.tool, result) }
})
```

`try/finally` em volta de `next(e)`: o resultado passa intacto, e o efeito colateral
(agendar refresh, abrir o painel na primeira edição) roda mesmo se a ferramenta falhou.
`afterTool` inspeciona `result.deny` e `result.isError` para saber se houve edição de fato.

## Injetar contexto com orçamento

Em `prompt.submit`, o botão "ask" de um arquivo faz os hunks dele pegarem carona no próximo
prompt:

```ts
const context = e.context ?? []
const text = Ask.fittedAskTextOf(
  asked.text,
  Limits.PROMPT_CONTEXT_MAX_CHARS - context.reduce((sum, entry) => sum + entry.length, 0),
)
if (text === undefined) { /* desarma e avisa a pessoa que não coube */ }
return next({ ...e, context: [...context, text] })
```

Dois detalhes que valem como regra geral:
- O orçamento é calculado **contra o que já está lá** — o plugin não assume que é o único
  contribuindo contexto.
- Quando não cabe, ele **desarma e avisa** (`"…'s diff did not fit in the prompt and was
  dropped"`), em vez de truncar em silêncio. Falha visível.

## Convenção de código: um conceito por diretório

252 arquivos `index.ts` em `hooks/`. O padrão é rígido:

```
hooks/git/fetch-diff/
  fetch-diff.ts     ← a definição
  index.ts          ← export * from './fetch-diff.js'
                      export * as default from '.'
```

O `export * as default from '.'` é o truque: permite `import Git from './git'` e usar
`Git.FileHunks`, `Git.fetchDiff` como namespace, sem um arquivo barril gigante escrito à mão.
Diretórios de topo em `hooks/`: `ask`, `backend`, `classify`, `git`, `host`, `limits`,
`names`, `pane-state`, `pane-toggle`, `record`, `todos`, `tools`, `turns`, `views`, e um
punhado de utilitários de uma função (`count-of`, `mtime-of`, `map-limited`, `is-record`).

Textos fixos ficam todos em `names/`; números fixos todos em `limits/` (`REDRAW_COALESCE_MS`,
`BODY_FETCH_CONCURRENCY`, `HEAD_POLL_MS`, `AUTO_OPEN_MIN_COLUMNS`, `PROMPT_CONTEXT_MAX_CHARS`).
Nenhum literal mágico espalhado.

## Disciplina de custo

O README do mod é explícito sobre **quando o git roda** — "git roda quando o do painel
built-in rodaria: nada no início da sessão; um `git rev-parse`, no diretório onde a sessão
começou, quando `/diff` ou a primeira edição com espaço para abrir precisa do repositório".

E há um teste dedicado a garantir isso (`tests/register.test.ts`: *"git runs at the built-in's
moments and no others"*), que conta os `git` disparados entre dois pontos. Um mod que roda
processo a cada evento seria invisível como bug e caro como comportamento; aqui virou
invariante testado.

Outras medidas no mesmo espírito: debounce de refresh, coalescência de redraw,
`mapLimited(..., BODY_FETCH_CONCURRENCY, ...)` para não disparar N `git diff` de uma vez,
poll de HEAD **só enquanto o painel está aberto**.

## Dependência entre mods, via `$`

`Host.mark` e `Host.log` chamam `$.telemetry.mark` / `$.telemetry.log` — substantivo que o
mod `telemetry` adiciona no fold `engine.create` ([10](10_mod_telemetry.md)). Um mod consome
outro **pelo `$`**, não por import. E quando o `telemetry` não está presente, o substantivo
não existe: "um plugin que chama `$.telemetry` onde este está ausente não acha o substantivo
e deve tratar isso como 'sem analytics aqui'" (`mods/telemetry/README.md`).

## Ver também

- [02](02_modelo_engine_hooks.md) — o modelo que este mod exercita
- [12](12_testing_kit.md) — os 199 arquivos de teste dele
- [10](10_mod_telemetry.md), [11](11_mod_sec_default.md) — os outros dois mods
