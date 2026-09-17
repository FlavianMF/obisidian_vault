---
title: Sistema de ferramentas — describe, check, call
type: project
tags: [claude-code, tool-use, permissions, schema]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Sistema de ferramentas

[← Índice](00_indice.md)

Três eventos cobrem o ciclo inteiro de uma ferramenta, e eles são deliberadamente
**separados por pergunta**, não por fase:

| Evento | Pergunta | Pode mudar a chamada? |
|---|---|---|
| `tool.describe` | Como o modelo enxerga esta ferramenta? | descrição |
| `tool.check` | Esta chamada **pode** rodar? | não — só decide |
| `tool.call` | A chamada roda | sim — reescreve, nega ou responde |

## `tool.describe` — o que o modelo lê

Dispara quando o engine renderiza o schema da ferramenta para o modelo pela primeira vez
(`claude-code.d.ts:3034`, `ToolDescribeInput` em 8102). `e.tool` é o nome como o modelo
vê (`Bash`, `mcp__server__tool`) e `e` traz a descrição como o engine a computou.

É o gancho de *prompt engineering sobre ferramenta*: dá para acrescentar avisos de política
("neste repo, `git push` exige branch"), sem tocar na implementação da ferramenta nem no
system prompt.

## `tool.check` — o gate de permissão

```ts
type ToolCheckDecision = 'allow' | 'ask' | 'deny'
```
`claude-code.d.ts:8042`.

- `allow` roda a ferramenta;
- `ask` entrega ao *decisor do modo* — o diálogo, o classificador do modo automático, ou um
  host headless;
- `deny` recusa, e o motivo vira o erro que o modelo lê.

`ToolCheckInput` (`claude-code.d.ts:8051`) carrega `tool`, `input` e `tool_use_id`, e **os
três são pinados**: "um hook decide sobre esta chamada, ele não a muda — `tool.call`
reescreve uma chamada". Separação limpa entre *julgar* e *agir*.

`ToolCheckResult` (8079): `{ decision, reason?, rule? }`. Vindo do core, é a decisão
declarativa do engine para o modo e as regras da sessão, e `rule` traz a regra de settings
**como escrita** (`Bash(git push:*)`) — ausente quando quem decidiu foi o modo ou o check da
própria ferramenta. Ou seja, a decisão é *explicável*, não um booleano.

Dois detalhes que importam para automação:

1. `tool_use_id` está **ausente numa consulta**. `$.tool.check(...)` roda a mesma cadeia e
   **não executa nada** (`claude-code.d.ts:2869-2871`): dá para perguntar "isso seria
   permitido?" sem efeito colateral.
2. `next.origin` diz quem levantou: `{ plugin: 'engine', tier: 'core' }` para a chamada do
   próprio modelo, ou o nome do plugin para um `$.tool.call` dele. Política pode distinguir
   "o modelo quer rodar isso" de "o plugin X quer rodar isso".

Ordem: `tool.check` dispara **depois** dos hooks `tool.call` e `PreToolUse`, e **antes** do
modo resolver um `ask` (`claude-code.d.ts:2857-2863`). Do core sobe o veredito do engine
(regras, modo, check da própria ferramenta, decisão do `PreToolUse`); um hook pode responder
qualquer veredito em qualquer direção, e **a última palavra subindo a cadeia é a decisão**.

## `tool.call` — a execução

```
'tool.call': ToolCallInput      // claude-code.d.ts:2855
```

> `next(e)` roda os hooks abaixo, depois o core (o prompt de permissão, a ferramenta em si).
> Retorne `{ deny: reason }` para recusar ou `{ result }` para responder você mesmo; um hook
> que retorna enquanto seu `next` está pendente aborta o que roda abaixo. **Os hooks de
> managed settings rodam primeiro: o deny deles é o resultado da chamada.**

`ToolCallResult` é uma união de duas formas (`claude-code.d.ts:7959`):

- `{ deny: string }` — o modelo recebe o texto como resultado de erro;
- `{ result, context?, ref?, text?, isError? }` — do core, `ref` nomeia as mensagens do core.

Quando um **hook** responde no lugar da ferramenta, o core não aceita de olhos fechados:

> O core valida a resposta de um hook contra o output schema da ferramenta quando ela tem
> um, mapeia para o modelo com o mapper da própria ferramenta, e grava na transcrição como
> resultado da ferramenta.

Isso é o que torna "mock de ferramenta" seguro: a resposta do plugin é forçada à mesma forma
que a real.

`ToolCallReserved` (`claude-code.d.ts:7943`) mostra as chaves que o envelope carrega e que a
ferramenta **não** vê — o engine as tira antes: `tool`, `tool_use_id` e `consent`. `consent`
é "as palavras da própria pessoa referentes ao aperto de tecla que levantou a chamada"
(`The user pressed "1: Yes" on ...`), e entra no contexto da execução como um turno humano,
que o caminho de permissão lê como pedido do usuário. Consentimento é **dado**, rastreável,
não um flag booleano perdido.

## Registrar ferramenta nova

```ts
type ToolSpec = { name: string; description: string; inputSchema?: Record<string, unknown> }
```
`claude-code.d.ts:8264`. Nome com letras/dígitos/`_`/`-`, até 64 caracteres;
**o modelo chama como `mcp__<plugin>__<name>`** — ou seja, uma ferramenta de plugin entra
pelo mesmo namespace de uma ferramenta de servidor MCP. `inputSchema` é JSON Schema, default
`{ type: "object" }`.

`$.tool.register` é um evento (`tool.register`, em `OpEventOf`), então registrar ferramenta é
interceptável como tudo o mais. O exemplo do docstring de `session.start` mostra o idioma:

```ts
on("session.start", ($, e, next) => $.tool.register(t).then(() => next(e)))
```
(`claude-code.d.ts:3114`) — o primeiro `session.start` é aguardado, então uma ferramenta
registrada ali já é listada no turno um.

## Ferramentas built-in, tipadas por declaration merging

`BuiltinToolInputs` e `BuiltinToolResults` (`claude-code.d.ts:610` e `630`) são interfaces
**vazias** no arquivo publicado. O comando `/plugin-types` escreve o conjunto da build
instalada embaixo das declarações do engine, a partir do output schema de cada ferramenta;
ferramenta sem schema fica `unknown`.

Consequência: depois de `e.tool === "Bash"`, o `result` de `next(e)` é o registro do Bash,
tipado. E consequência para esta pesquisa: **a lista de ferramentas built-in não está no
repo** — ela é gerada localmente, por versão. O repo publica o *mecanismo*, não o inventário.

## O resto do mundo também é ferramenta, em certo sentido

O que um plugin pode fazer fora das ferramentas do modelo está em `$` e é igualmente
enganchável (ver [03](03_event_surface.md)): `fs.read/write/list/exists/stat/ancestors`,
`process.run`, `http.fetch`, `env.get/set`, `mcp.call`, `store.get/set/delete/keys`.

A diferença entre "ferramenta" e "capacidade" aqui é só **quem chama**: a ferramenta é
chamada pelo modelo e passa por `tool.check`; a capacidade é chamada pelo plugin e passa
pelos hooks acima dele. O mecanismo de interceptação é o mesmo.

## `ToolUseSummary` — a visão da transcrição

`ToolUseSummary` (`claude-code.d.ts:8285`) é como uma chamada
aparece já pareada com seu resultado (`tool_use_id`), com `input`, `result`, `text` e
`isError`. Um detalhe operacional registrado ali: **em headless (`-p`), uma ferramenta pode
guardar o registro sem o volume** — o Bash zera `stdout` — mas `text` existe de qualquer
forma. Relevante para quem for minerar transcrições de sessão automatizada
(ver [16](16_runtime_local_observado.md)).

## Ver também

- [06](06_permissoes_seguranca.md) — as regras e modos por trás do veredito do core
- [13](13_mcp.md) — `mcp.call` e o namespace `mcp__server__tool`
- [09](09_mod_diff.md) — um mod real usando `process.run` e `ui.*`
