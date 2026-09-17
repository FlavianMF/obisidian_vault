---
title: O loop do agente — turno, passo, compactação
type: project
tags: [claude-code, agent-architecture, llm, streaming, context-management]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# O loop do agente: turno, passo, compactação

[← Índice](00_indice.md)

O loop não é um bloco opaco: ele é **descrito evento a evento** no contrato
(`mods/types/claude-code.d.ts`). Este capítulo reconstrói o loop a partir dos eventos, na
ordem em que disparam.

## A forma do loop

```
session.start          uma vez por plugin carregado, antes do primeiro prompt
  │
  ├─ prompt.submit     o texto que a pessoa mandou
  │
  turn.start           o turno começa; o turnId é cunhado AQUI
  │
  ├─ turn.step  index=0   ┐ uma requisição de modelo
  │   └─ (stream de chunks)│ o resultado inclui toolUses[]
  ├─ tool.check           │ pode rodar?
  ├─ tool.call            │ roda
  ├─ turn.step  index=1   │ próxima requisição, com os resultados das ferramentas
  │   ...                 ┘ repete até o modelo parar de chamar ferramenta
  │
  turn.complete        o turno acabou; `e.reason` diz por quê
```

Com `session.compact` cortando transversalmente, quando o contexto estoura.

## `turn.start` — 34 linhas de contrato, um fato importante

```ts
type TurnStartInput = { text: string; turnId: string }
```
`claude-code.d.ts:8477`.

- `text` é `""` num turno sem prompt digitado (uma continuação).
- `turnId` é **cunhado aqui** e carregado por todo `turn.step` e pelo `turn.complete`
  daquele turno.
- É **puramente observacional**: "um valor diferente não muda o turno"
  (`TurnStartResult`, `claude-code.d.ts:8492-8495`).

Esse é o ponto de ancoragem para correlacionar tudo o que acontece num turno — o
equivalente a um trace id.

## `turn.step` — o ponto de interceptação de LLM

É aqui que mora o poder real. Docstring, `claude-code.d.ts:3176-3182`:

> Dispara quando o engine está prestes a mandar uma requisição de modelo de um turno, do
> main ou de um subagente (`e.agentId`); `next(e)` resolve para a resposta inteira.
> `next({ ...e, model })` ou `effort` manda outra; o turno, o índice e a contagem de
> mensagens são pinados. **Uma resposta sem `next` não manda requisição nenhuma.**
> Toda requisição do turno passa aqui; `turn.complete` segue a última.

`TurnStepInput` (`claude-code.d.ts:8532`):

| Campo | Reescrevível? | O que é |
|---|---|---|
| `turnId` | pinado | o turno |
| `index` | pinado | posição do passo no turno, de 0 |
| `model` | **sim** | o modelo que a requisição nomeia, já resolvido para este passo |
| `effort` | **sim** | `low \| medium \| high \| xhigh \| max \| number` |
| `messageCount` | pinado | quantas mensagens a requisição carrega |
| `agentId` | pinado | o loop em que a requisição é feita; ausente no main |

**A transcrição não está em `e`.** Só a contagem; para ler as mensagens, `$.session.messages()`
— que é ele próprio um evento (`session.messages`, ver [03](03_event_surface.md)). Separar
"metadado da requisição" de "conteúdo da conversa" mantém o payload de hook pequeno e torna
a leitura da conversa uma ação auditável, não um dado que chega de graça.

`TurnStepResult` (`claude-code.d.ts:8592`): `{ turnId, index, answer, toolUses[], stopReason, usage }`.
`usage` é o custo como a API reportou, e `null` quando nenhuma resposta chegou.
**Um hook que devolve valor próprio muda o que os hooks acima leem, nunca o que o engine
streamou** (`claude-code.d.ts:8586-8590`) — a transcrição real fica protegida.

### Streaming tipado

A resposta atravessa a cadeia em chunks, `TurnStepChunk` (`claude-code.d.ts:8505`):

| Kind | Conteúdo |
|---|---|
| `text` | texto visível |
| `thinking` | raciocínio |
| `tool` | início de chamada de ferramenta |
| `input` | pedaço do JSON dos argumentos, parcial |
| `stop` | parada |
| `engine` | **opaco**, só `ref: number` — o envelope, começo/fim de bloco, marca de retry |

Texto, thinking, chamadas e parada são "dados planos que um hook lê e reescreve"; o resto
passa sem ser lido (`claude-code.d.ts:8501-8504`). O que sai do hook mais externo é o que é
mostrado e gravado.

Detalhe de robustez: os argumentos de uma ferramenta são os pedaços `input` concatenados e
parseados **uma vez**, no fim do bloco; pedaços que não parseiam deixam a chamada sem
argumentos — "como um modelo que escreveu JSON quebrado faria" (`claude-code.d.ts:8578-8582`).
Falha explícita, sem adivinhação.

## `turn.complete`

Dispara quando o turno acabou, no ponto em que a duração é reportada; `next(e)` resolve
`{ text }`, a resposta. Retornar `{ text }` diferente **mostra o texto abaixo da resposta**
(uma sinopse, um TL;DR) — "a gravação da transcrição nunca é reescrita"
(`claude-code.d.ts:3185-3191`). Hook que falha deixa a resposta como estava.

De novo o mesmo princípio: um plugin pode **acrescentar** à apresentação, nunca **falsificar**
o registro.

## `session.compact` — compactação como evento de primeira classe

`SessionCompactInput` (`claude-code.d.ts`, tipo homônimo):

| Campo | Reescrevível? | O que é |
|---|---|---|
| `trigger` | pinado | o que disparou: `/compact`, o limiar, um plugin, ou `precompute` |
| `agentId` | pinado | o loop que compacta; ausente no main |
| `instructions` | **sim** | o que o resumo deve manter ou enfatizar |
| `messages` | **sim** | a transcrição sendo compactada |

Três saídas: reescrever na descida, reescrever na subida, ou `{ skip: reason }` — que deixa
a conversa como está (`claude-code.d.ts:3130-3139`).

Duas decisões de design dignas de nota:

1. **"Não existe string de resumo: o resumo é uma mensagem"** (`SessionCompactResult`).
   Compactação produz transcrição, não um campo especial. Uniformidade de representação.
2. Uma mensagem mantida **com seu `handle`** é a mensagem original do engine, inteira; uma
   sem handle é lida como construída. Ou seja: o hook pode selecionar o que sobrevive sem
   ter que reserializar — e o engine sabe distinguir o que é autêntico do que o plugin
   inventou.
3. Existe um trigger `precompute`: compactar **antes** de precisar. O exemplo do próprio
   docstring é desligá-lo: `on("session.compact", { trigger: "precompute" }, () => ({ skip: "off" }))`.

## `session.receive` — a entrada que não é o teclado

Dispara quando uma entrega chega à sessão — evento de um relay, mensagem de um peer, prompt
de Remote Control — **antes de ser enfileirada** (`claude-code.d.ts:3117-3127`).
Retornar `{ consumed: reason }` toma a entrega: nada é enfileirado, mostrado ou lido pelo
modelo. O dual, `session.send`, está **reservado** (declarado no contrato mas não servido).

Isso mostra que o loop já não pressupõe um humano num terminal: entradas vêm de vários
lados, e cada uma passa por um ponto de política único.

## Onde os subagentes entram

`agentId` aparece em `turn.step`, em `session.compact` e nos `tool.call` — o mesmo loop,
identificado. E há uma regra de origem que evita recursão indesejada:

> Um subagente que um hook criou por `$.agent.spawn` **pula aquele hook** nos seus passos,
> como fazem suas chamadas de ferramenta; todo outro hook vê os passos dele.
>
> — `claude-code.d.ts:8556-8559`

Detalhe em [14](14_subagentes_skills_comandos.md).

## Ver também

- [03](03_event_surface.md) — o catálogo dos eventos
- [05](05_sistema_tools.md) — o que acontece entre `turn.step` e o próximo
- [07](07_prompt_contexto_memoria.md) — como o prompt que vai em `turn.step` é montado
