---
title: Prompt, contexto e memória
type: project
tags: [claude-code, prompt-engineering, context-management, prompt-caching]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Prompt, contexto e memória

[← Índice](00_indice.md)

Seis eventos cobrem a montagem de tudo que o modelo lê antes da conversa. O desenho aqui tem
uma preocupação atravessada que não aparece nos outros subsistemas: **cache de prompt**.

## Os eventos, em ordem de montagem

| Evento | Frequência | `next(e)` resolve |
|---|---|---|
| `prompt.section` | uma vez **por seção nomeada** do system prompt | `{ text }` |
| `prompt.context` | uma vez **por conversa** | `{ blocks }` |
| `tool.describe` | uma vez **por ferramenta** | `{ description }` |
| `skill.prompt` | quando uma skill computa seu prompt | `{ text }` |
| `prompt.fill` | quando texto entra na caixa de prompt | o texto |
| `prompt.suggest` | quando uma sugestão dim é proposta | `{ isShown }` |
| `prompt.submit` | quando um prompt é submetido | antes do turno começar |

## `prompt.section` — o system prompt é nomeado por seção

```ts
type PromptSectionInput  = { name: string; text: string | null }
type PromptSectionResult = { text: string | null }
```

O system prompt não é uma string monolítica: é uma lista de seções **com nome**
(`env_info_simple`, `memory`, …), e cada uma passa por um evento. `text` é o que o core
computou, ou `null` quando o core omite a seção. Devolver `{ text: null }` deixa a seção de
fora:

```ts
on("prompt.section", { name: "memory" }, () => ({ text: null }))
```
(exemplo do contrato, `claude-code.d.ts:3016`.)

Isso é bem mais cirúrgico do que "anexar ao system prompt": dá para **substituir** a memória,
o bloco de ambiente ou qualquer outra seção, por nome, sem tocar no resto.

## A regra de cache, dita explicitamente

> Seções são cacheadas por nome pela duração da sessão até
> `$.ui.invalidate("prompt.section")`: **uma resposta instável gasta o cache de prompt do
> modelo a cada chamada**. Um hook que falha deixa passar.
>
> — `claude-code.d.ts:3011-3014`

E igual para ferramentas:

> Schemas renderizados são cacheados pela sessão até `$.ui.invalidate("tool.describe")`:
> uma resposta instável gasta o cache de prompt do modelo a cada chamada.
>
> — `claude-code.d.ts:3028-3031`

Duas coisas dignas de nota para quem projeta harness:

1. A **invalidação é explícita** (`$.ui.invalidate(<evento>)`), não por TTL nem por
   heurística. O plugin declara quando sua resposta mudou.
2. O custo econômico do plugin está **documentado no contrato**. Um plugin que devolve
   timestamp numa seção quebra o prompt caching de toda a sessão e o autor foi avisado no
   lugar certo — o docstring do evento que ele vai hookar.

## `prompt.context` — os blocos da primeira mensagem

Dispara **uma vez por conversa**, quando o engine computa os blocos de contexto que a primeira
mensagem de usuário carrega. O hook pode "anexar, remover, reordenar ou reescrever" com
`next({ ...e, blocks })`. O engine renderiza o que voltar, na ordem, até
`$.ui.invalidate("prompt.context")` **ou uma releitura (compactação, `/clear`)`**.

`on("prompt.context", () => ({ blocks: [] }))` — o exemplo do contrato — zera o contexto
inicial inteiro.

Note a assimetria deliberada: `prompt.context` é da *conversa*; `prompt.submit` é de *cada
prompt* e o contexto que ele anexa é aditivo. O `sec-default` protege o primeiro e deixa o
segundo aberto ao usuário ([11](11_mod_sec_default.md)) — é a fronteira entre "o que a
organização estabelece" e "o que a pessoa acrescenta".

## `prompt.submit`

> Dispara quando um prompt é submetido, antes do turno começar. `next(e)` roda os hooks
> abaixo **e os hooks de settings `UserPromptSubmit`**.
> Reescreva com `next({ ...e, text })` (a mensagem do usuário na tela acompanha) ou pare com
> `{ drop: reason }`; **um plugin quebrado nunca bloqueia um prompt**.
> Um prompt digitado enquanto um turno rodava dispara no Enter, com o id daquele turno.
>
> — `claude-code.d.ts:2966-2973`

Três detalhes:
- É aqui que a ponte com o hook clássico `UserPromptSubmit` acontece — o clássico roda
  *abaixo* do novo.
- "A mensagem do usuário na tela acompanha" a reescrita: nada de divergência entre o que a
  pessoa vê e o que o modelo lê.
- "Um plugin quebrado nunca bloqueia um prompt" — a política de falha do harness
  ([02](02_modelo_engine_hooks.md)) é reafirmada no ponto mais sensível.

`PromptSubmitInput` traz `text` "como vai chegar ao modelo (pastes já expandidos)", e um campo
presente só quando a submissão carregou imagens ou itens não textuais. `context` é "dos hooks,
para anexar" — `origin`, `turnId` e `wait` são do engine (`PromptSubmitArgs`).

O `diff` usa exatamente isso para fazer os hunks de um arquivo pegarem carona no próximo
prompt, com orçamento de caracteres ([09](09_mod_diff.md)).

## `prompt.fill` e `prompt.suggest` — a caixa de texto

Dois eventos sobre a *caixa*, não sobre a conversa:

- `prompt.fill` — quando um texto entra na caixa.
  `on("prompt.fill", ($, e, next) => next({ ...e, text: e.text.trim() }))`.
- `prompt.suggest` — quando uma sugestão dim é proposta, Tab para aceitar: "o palpite do
  engine depois de um turno, ou o `$.prompt.suggest` de um plugin". `{ isShown: false }`
  sem `next` descarta; "o core responde isso também enquanto a caixa tem texto ou um turno
  roda".

Um harness que queira autocompletar ou templates de prompt tem ponto de entrada sem tocar em
nada do loop.

## `skill.prompt` e memória

`skill.prompt` é minimalista — `{ skill, text }` entra, `{ text }` sai
([14](14_subagentes_skills_comandos.md)).

A **memória** (`CLAUDE.md`) aparece por três caminhos distintos, o que vale notar:

1. Como seção do system prompt: `prompt.section` com `name: "memory"`.
2. Como hook clássico: `InstructionsLoaded` ([03](03_event_surface.md)).
3. Como conteúdo gerenciado que o `sec-default` protege — "CLAUDE.md gerenciado, regras e
   skills de política chegam ao modelo como escritos" ([11](11_mod_sec_default.md)).

E `ContextMemoryFile` (`claude-code.d.ts:1713`) existe como tipo de primeira classe na
descrição do contexto, ao lado de `ContextSkill`, `ContextMcpTool`, `ContextSlashCommands`,
`ContextAgent` e `ContextApiUsage` — ou seja, o harness modela "o que está ocupando a janela
de contexto" como dado estruturado, por categoria (`ContextCategory`,
`ContextCategoryKind: 'used' | 'free' | 'buffer' | 'deferred'`, `claude-code.d.ts:1618-1655`).

## `attribution.text`

`AttributionTextKind = 'commit' | 'pr' | 'exemption' | 'remedy'` (`claude-code.d.ts:383`).
É o evento que produz as linhas de atribuição — a `Co-Authored-By` de um commit, o rodapé de
um PR. Também protegido pelo `sec-default`: uma organização pode exigir uma atribuição que
nenhum plugin de usuário remove.

## Ver também

- [04](04_agent_loop_turn.md) — `session.compact`, o outro lado da gestão de contexto
- [05](05_sistema_tools.md) — `tool.describe` na perspectiva de ferramentas
- [11](11_mod_sec_default.md) — quais destes eventos a organização protege
