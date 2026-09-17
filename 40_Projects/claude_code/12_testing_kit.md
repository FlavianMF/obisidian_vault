---
title: O kit de teste claude-code/testing
type: project
tags: [claude-code, testing, mocking, plugins]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# O kit de teste: `claude-code/testing`

[← Índice](00_indice.md)

O segundo módulo declarado no `.d.ts` (`declare module 'claude-code/testing'`,
`claude-code.d.ts:9448`) é o kit que `claude plugin test <dir>` roda. Vale um capítulo
próprio porque a forma dele é **consequência direta** do modelo de eventos — e é a parte mais
copiável do desenho inteiro.

## A ideia em uma frase

> Um teste recebe o próprio `$` do engine e o `on` de um plugin. Cada chamada em `$` é uma
> que o engine faz, através de cada hook do mod carregado como ele é distribuído. Os hooks
> que o teste registra com `on` sentam **abaixo** do mod, onde o resto do mundo estaria, e
> **nada fica abaixo deles**: uma chamada que eles deixam sem resposta lança, nomeando o
> evento.
>
> — `mods/README.md`

Releia a última parte. Não existe mock de biblioteca, não existe injeção de dependência, não
existe `jest.mock`. O teste **é um plugin**, sentado no fundo da cadeia, e ele é o mundo.

Isso só funciona porque [todo acesso ao mundo já é um evento](02_modelo_engine_hooks.md).
O que noutro desenho exigiria um framework de mock, aqui é o mecanismo normal usado ao
contrário.

## A forma de um arquivo de teste

```ts
import { describe, expect, mock, test, tier } from 'claude-code/testing'

tier('builtin')

describe('register', () => {
  test('fora de um repositório git o /diff diz isso e não abre nada', async ($, on) => {
    const opened: string[] = []
    mock.clock(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('command.register', ($, e) => ({ value: { command: e.name } }))
    on('process.run', () => ({ value: { exitCode: 128, stdout: '', stderr: 'fatal: not a git repository' } }))
    on('ui.open', ($, e, next) => { opened.push(e.id); return next(e) })

    await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
    const { text } = await $.command.run({ command: 'diff', args: '', origin: { kind: 'composer' } })

    expect(text).toContain("isn't in a git repository")
    expect(opened).toEqual([])
  })
})
```
(exemplo do `mods/README.md`.)

Quatro papéis num arquivo só:

- **`tier('builtin')`** — em que tier o plugin sob teste carrega (`claude-code.d.ts:9951`).
  `prepend`, `user` (o default), `append` ou `builtin`. **O teste declara o assento**, porque
  o assento muda o comportamento ([11](11_mod_sec_default.md)).
- **`$`** — o `$` do próprio engine: "cada chamada nele é feita como o REPL, o loop de query
  e os sites de render fazem as suas, sobre cada plugin" (`Engine`, `claude-code.d.ts:9499`).
  Chamar `$.command.run(...)` é *ser o usuário digitando `/diff`*.
- **`on`** — registra hooks abaixo de todo plugin. É o mundo.
- **`expect`** — matchers no estilo Jest, com `.not`, `.resolves`, `.rejects`,
  `expect.any`, `expect.objectContaining`, `arrayContaining`, `stringMatching`.

## `mock` — três substantivos, de memória

`Mock` (`claude-code.d.ts:9768`) tem exatamente três membros, e cada um é "uma função simples
sobre `on` que registra hooks onde o teste a chama":

| Membro | Responde | Detalhe |
|---|---|---|
| `mock.clock(on, options?)` | `$.clock` | Relógio em memória que **só anda quando o teste o move** |
| `mock.store(on, entries?)` | `$.store` | `get`/`set`/`delete`/`keys` em memória |
| `mock.env(on, variables)` | `$.env.get` | Variável não listada é não definida |

O relógio é a peça mais bem pensada (`MockClock`, `claude-code.d.ts:9812`):

- `clock.advance(ms)` resolve cada espera vencida no caminho (`$.clock.sleep`, `after`,
  `every`) **na ordem em que vencem**; o que uma espera iniciou roda antes de a próxima
  resolver.
- Uma espera pendurada além do orçamento de um hook (**dez segundos de tempo real**) é
  solta, "como um hook que estourou".
- `await clock.settle()` — "para ver o que um dispatch faz antes de responder, comece-o sem
  `await`, dê `settle()`, e olhe: o relógio fica onde estava" (`mods/README.md`).

Isso resolve o problema clássico de testar código com debounce, poll e coalescência — que é
exatamente o que o `diff` tem ([09](09_mod_diff.md)).

## `$.ui.press` — apertar botão como a pessoa aperta

`EnginePress` (`claude-code.d.ts:9527`): `$.ui.press({ plugin, key, requestId? })` é
"o terminal apertando um Button que o teste renderizou: a cadeia `ui.press` sobre cada plugin
hookado nela, o `onPress` do próprio Button no fundo".

Rejeita quando nenhum Button daquele tipo está desenhado, ou quando há vários e nenhuma
instância foi nomeada. Teste de UI sem DOM e sem snapshot: a UI é um evento como os outros.

## Ambiente e limites

- O ambiente do teste é "como aquele em que os hooks de um plugin rodam (sem fs, rede ou
  processo)", com o plugin carregado da pasta pelo próprio host do engine
  (`claude-code.d.ts:19-22`).
- **Os plugins carregam na primeira chamada em `$`**, então o teste registra seus hooks antes
  dela — "como um módulo registra os seus em `register()`" (`TestBody`, `claude-code.d.ts:9923`).
- Timeout padrão 5000 ms, ajustável por `TestOptions.timeoutMs`.
- `TestOptions.plugins` carrega plugins inline ao lado do que está sob teste: `{ name, tier?, register }`.
  Serve para testar **interação entre plugins de tiers diferentes** — ou seja, dá para testar
  o `sec-default` contra um plugin de usuário hostil.
- Uma falha "carrega o que o engine reportou nesse meio-tempo: cada hook que ele pulou, e por
  quê" (`claude-code.d.ts:9908-9909`). Como hook que falha é silenciosamente ignorado em
  produção ([02](02_modelo_engine_hooks.md)), o teste precisava expor isso — e expõe.

## Organização dos arquivos

Do `mods/README.md`:

> Um arquivo de teste é nomeado pelo que cobre sob `hooks/` (`register.test.ts` ao lado de
> `hooks/register.ts`, `git.test.ts` ao lado de `hooks/git/`), e guarda seus imports, o tier
> em que o mod carrega, e **um** `describe` intitulado com esse nome; o que vários testes
> compartilham fica sob `tests/fixtures/`, um export por arquivo.

No `mods/diff`: 199 arquivos de teste espelhando `hooks/`, mais `tests/fixtures/`
(`in-repository.ts`, `repository-of/`, `branch-base-of/`, `typed-prompt-of.ts`, …).

## O teste que vale citar

`mods/diff/tests/register.test.ts` (669 linhas) tem um caso chamado
**"git runs at the built-in's moments and no others"**. Ele conta os processos `git`
disparados entre pontos do roteiro:

```ts
await $.session.start(Fixtures.SESSION)
await $.ui.render(Fixtures.hintAt(Limits.AUTO_OPEN_MIN_COLUMNS - 1))
await world.clock.advance(Fixtures.SETTLE_MS)
expect(spawnedSince(), 'o início e o rodapé: nada').toEqual([])

await edit(); await world.clock.advance(Fixtures.SETTLE_MS)
expect(spawnedSince(), 'uma edição sem espaço para painel: nada, a largura é lida antes').toEqual([])

await $.command.run(Fixtures.DIFF); await world.clock.advance(Fixtures.SETTLE_MS)
expect(spawnedSince(), '/diff: encontrado, depois um fetch para o painel')
  .toEqual(['rev-parse --show-toplevel', 'status', 'diff --shortstat', /* ... */])
```

Isso é um teste de **custo**, não de comportamento: garante que o plugin não gasta processo
onde o built-in não gastaria. Num harness onde plugins de terceiros rodam no caminho quente,
esse tipo de asserção é o que impede degradação invisível.

Repare também no segundo argumento de `expect` — uma frase em prosa que vira a mensagem da
falha. Todo o repo usa isso.

## Typecheck

```
tsc -p mods/tsconfig.json     # typecheca hooks e testes de todo mod
claude plugin test mods/diff  # roda os testes
claude --plugin-dir mods/diff # roda o mod a partir do source
```
(`mods/README.md`.) O `tsconfig` que serve um módulo de hooks está no cabeçalho do
`.d.ts` (`claude-code.d.ts:33-52`): `target es2023`, `types: []`, `moduleResolution: bundler`,
`strict`, `noUncheckedIndexedAccess`, `jsx: react` com `jsxFactory: h`, e
`lib: ["es2023"]` **sem DOM** — porque não há DOM e o `Text` dele sombrearia o elemento.

> Nota desta pesquisa: os três comandos acima estão documentados no `mods/README.md`.
> **Não foram executados** aqui — o repo foi clonado só para leitura e o mod `telemetry`
> nem carrega fora de build interno ([10](10_mod_telemetry.md)).

## Ver também

- [02](02_modelo_engine_hooks.md) — por que o teste pode ser um plugin
- [09](09_mod_diff.md) — o código que esses 199 testes cobrem
- [08](08_plugins_e_mods.md) — `claude plugin test` entre os comandos de plugin
