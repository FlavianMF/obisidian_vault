---
title: O modelo engine/hooks — $, on, next e os cinco tiers
type: project
tags: [claude-code, agent-architecture, plugin-api, middleware]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# O modelo central: engine, `$`, hooks e tiers

[← Índice](00_indice.md)

Tudo em Claude Code que é extensível passa por **um único modelo**, declarado em
`mods/types/claude-code.d.ts`. Vale a pena entendê-lo antes de qualquer outra coisa:
os capítulos seguintes são detalhamento dele.

## A frase que resume

> Um mod é um plugin do Claude Code cujo comportamento vive num módulo de hooks: um
> `register(on, options)` que engancha os eventos do engine como funções `($, e, next)`.
>
> — `mods/README.md:3-5`

Três nomes, e só três:

| Nome | O que é |
|---|---|
| `$` | O **mundo**: tudo que o plugin pode fazer. `EngineInterface`, congelado. |
| `on` | O **registro**: engancha um hook num evento. Só existe dentro de `register`. |
| `next` | O **resto da cadeia**: o que roda abaixo deste hook, até o core. |

```ts
export const register: Register = (on, options) => {
  on("tool.call", ($, e, next) => e.tool === "Bash" ? { deny: "no" } : next(e))
}
```
(`claude-code.d.ts:5901`, com o exemplo no próprio docstring de `Register`.)

## A inversão que faz o design funcionar

O ponto não óbvio, e o mais importante para quem projeta um harness:

> Os eventos são as chamadas em `$` que o host serve: `e` é o argumento da chamada
> quando ela cruza para o host, e toda uma delas é enganchável pelo nome e por `on("*")`.
>
> — `claude-code.d.ts:4478` (`OpEventOf`)

Ou seja: **não existem duas superfícies** — uma "API que o plugin chama" e outra "eventos
que o plugin escuta". É a mesma. Quando um plugin chama `$.fs.write(...)`, isso é um
*dispatch* que os hooks acima dele veem, podem reescrever, negar (`{ deny }`) ou responder
sozinhos (`{ value }`). O core é apenas a implementação mais interna (`EventOf = CoreEventOf & NounEventOf`,
`claude-code.d.ts:3449`).

Consequências diretas:

- Auditar tudo que qualquer plugin faz = um hook `on("*")`.
- Sandboxar um plugin = um hook acima dele que nega certos eventos.
- Simular o mundo num teste = registrar hooks abaixo do mod que respondem de memória
  (é exatamente como o kit de teste funciona — ver [12](12_testing_kit.md)).
- Um plugin que só observa não precisa de API nenhuma nova: o evento já existe.

## Os cinco tiers

```
const TIERS: readonly ["prepend", "user", "append", "builtin", "core"]
```
`claude-code.d.ts:7870`. **Mais externo = mais autoridade.**

| Tier | Quem senta aqui |
|---|---|
| `prepend` | Plugins gerenciados que um administrador prefixa |
| `user` | Tudo que a pessoa instala |
| `append` | Plugins gerenciados que o administrador acrescenta |
| `builtin` | Plugins embutidos no binário (os três mods — ver [08](08_plugins_e_mods.md)) |
| `core` | O elo mais interno: o engine em si |

Hooks do mesmo evento aninham nessa ordem **e em nenhuma outra** (`claude-code.d.ts:7860-7872`).
É isso que dá a garantia de segurança: um hook `user` nunca envolve um hook `prepend`, logo
política organizacional não é contornável por plugin instalado pelo usuário — a base do mod
`sec-default` ([11](11_mod_sec_default.md)).

`next.to(e, tier)` pula elos, mas **só para dentro**: "prepend pode nomear append, builtin
ou core; append só core; nunca pula um tier com mais autoridade, então nenhum hook de
usuário pula o da organização" (`claude-code.d.ts:4278-4283`). Os elos pulados ficam no
`trace`.

## O que um hook recebe e o que pode devolver

`($, e, next)` — assinatura única para todo evento (`Hook`, `claude-code.d.ts:3615`).

- **`$`** — congelado, o mesmo objeto em toda invocação. Não carrega `on`: registro
  acontece antes de `$` existir (`claude-code.d.ts:3203-3214`).
- **`e`** — congelado **em toda profundidade**. `e.command = "ls"` é erro de tipo *e*
  lança em runtime. Reescrever = passar uma cópia para `next` (`claude-code.d.ts:3462-3466`).
- **`next`** — chamável, mas também um objeto com:

| Membro | Para quê |
|---|---|
| `next(e)` | Continua a cadeia com este evento (possivelmente reescrito) |
| `next.to(e, tier)` | Continua pulando até um tier, só para dentro |
| `next.signal` | `AbortSignal`: a chamada foi abandonada (usuário interrompeu, hook acima respondeu antes, estourou o orçamento) |
| `next.is(pattern, e)` | Type predicate — para hooks glob (`on("*")`) estreitarem o tipo |
| `next.event` | O nome do evento, como valor |
| `next.origin` | `{ plugin, tier }` de quem originou o dispatch. **Escrito só pelo host**, a partir do `MessagePort` de onde veio a chamada — nada que o plugin escreva chega aqui |
| `next.trace` | O que se resolveu abaixo deste hook, um item por elo, mais próximo primeiro |

(`claude-code.d.ts:4270-4330`.)

Retornos possíveis: `next(e)` (passa adiante), `{ deny: reason }` (recusa),
`{ value }` / `{ result }` (responde sozinho, o que está abaixo nem roda).
Um hook que retorna enquanto seu `next` ainda está pendente **aborta o que roda abaixo**
(`claude-code.d.ts:2850-2852`).

## Falha de hook é isolada, não fatal

`on(...)` devolve uma `Registration`, que aceita **um** `.catch` (`claude-code.d.ts:5905-5920`).
Sem `.catch`, um hook que falha simplesmente **não existe** para aquele dispatch — a cadeia
segue. Há orçamento de tempo por hook; estourar conta como falha. Exceção: `engine.create`,
cujo hook não tem orçamento e cuja falha é a falha do *load* do plugin.

## `engine.create`: o fold que monta o `$`

O único evento que roda antes de tudo, uma vez por load/reload de cada plugin:

> Um passo pode ADICIONAR substantivos e RETER substantivos (deixar um de fora, ou
> retornar sem `next`); não pode SUBSTITUIR um que outro passo adicionou: o passo falha,
> nomeando os dois plugins.
>
> — `claude-code.d.ts:3197-3200`

Dentro do hook `engine.create`, `$` é `NoEngineInterface`: toda propriedade é `never`, então
`$.model` ali é erro de compilação (`claude-code.d.ts:4363`). `$` só existe *depois* do fold.

Isso dá duas capacidades de uma vez, com um mecanismo só:

- **Estender**: um plugin adiciona um substantivo ao `$` (é assim que `telemetry` publica
  `$.telemetry` — ver [10](10_mod_telemetry.md)). O substantivo vira evento automaticamente
  (`NounEventOf`, `claude-code.d.ts:4413`), logo é enganchável como qualquer outro.
- **Reter**: um plugin externo pode omitir um substantivo do `$` que os plugins internos
  recebem. Um substantivo retido aparece como stub e o host recusa a operação
  (`claude-code.d.ts:3226-3232`). É capability-dropping por construção.

Tipagem entre plugins: um plugin que adiciona um substantivo publica um `.d.ts` que o
`plugin.json` nomeia em `"types"`, com declaration merging em `EngineInterface` — "do jeito
que um plugin de jQuery tipa `$.fn`" (`claude-code.d.ts:3211`, e o cabeçalho, linhas 55-63).

## O ambiente onde um hook roda

Não é Node e não é browser (`claude-code.d.ts:14-18`):

- Sem DOM, sem `fs`, sem `process`, sem rede direta. Acesso ao mundo só via `$` — o que
  é justamente o que torna todo acesso enganchável.
- Tem as web APIs (`URL`, `TextEncoder`, `AbortController`, `crypto.subtle`, ...).
- Tem `h` e `Fragment` globais: JSX compila contra eles. Os elementos de desenho
  (`Box`, `Text`, `Button`) **não** são globais — vêm da tabela da superfície,
  `const { Box, Text } = $.ui.resolve(e)`.
- Cada plugin roda no seu próprio ambiente, com `MessagePort` próprio — é daí que o host
  deriva `next.origin` sem confiar no plugin.

## Hooks "classic" continuam existindo

Os hooks JSON de sempre (`PreToolUse`, `UserPromptSubmit`, `SessionStart`, ...) não foram
substituídos: foram **absorvidos** como eventos `classic.<Nome>`
(`ClassicEventName = \`classic.${ClassicHookEvent}\``, `claude-code.d.ts:774`). São 33 nomes
(lista em [03](03_event_surface.md)), e o resultado deles é normalizado em `ClassicResult`
(`claude-code.d.ts:809`), onde vários hooks de settings dobram num só — última escrita vence,
contextos concatenam.

Leitura prática: a superfície nova é um superconjunto estrito da antiga, e um harness
próprio pode adotar o modelo novo sem quebrar automação existente.

## Para o harness próprio

O que este capítulo vale como padrão está destilado em
[20](20_implicacoes_harness_capella.md); o contraste com o desenho do opencode (permissão
como *deferred promise*, hooks de plugin como lista fixa de pontos) está em
[19](19_comparativo_opencode.md).

## Ver também

- [03](03_event_surface.md) — o catálogo completo de eventos
- [08](08_plugins_e_mods.md) — como isso é empacotado como plugin/mod
- [12](12_testing_kit.md) — como o modelo torna o teste trivial
