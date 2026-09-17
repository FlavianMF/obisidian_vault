---
title: Configuração e settings
type: project
tags: [claude-code, configuration, settings, provenance]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Configuração e settings

[← Índice](00_indice.md)

Dois sistemas distintos, que é fácil confundir:

| | **Settings** | **Config** |
|---|---|---|
| O que é | Arquivos JSON, hierárquicos, escritos por pessoa/projeto/organização | As linhas do menu `/config` |
| Superfície | `settings.read` | `config.list`, `config.set`, `config.describe` |
| Quem escreve | Humano ou MDM, fora da sessão | A pessoa no menu, ou um plugin |

## Settings: cinco fontes, precedência crescente

```ts
type SettingsSource = 'user' | 'project' | 'local' | 'flag' | 'policy'
```
`claude-code.d.ts` (`SettingsSource`). A ordem é **a de menor precedência primeiro**:

| Fonte | Arquivo / origem |
|---|---|
| `user` | `~/.claude/settings.json` |
| `project` | `.claude/settings.json` |
| `local` | `.claude/settings.local.json` |
| `flag` | o que `--settings` e os settings inline do SDK carregam |
| `policy` | os managed settings, **todos os tiers gerenciados já mesclados** |

Leitura por plugin:

```ts
$.settings.read()                      // mesclado sobre todas as fontes, como o engine roda
$.settings.read({ source: 'policy' })  // uma fonte só, como carregada
```
(`SettingsReadArgs`.) A distinção importa: é exatamente com `{ source: 'policy' }` que o
`sec-default` lê a política sem poder ser enganado pelo que um plugin de usuário reescreveu
no merge ([11](11_mod_sec_default.md)) — e por isso ele também empurra `settings.read`
inteiro para além do tier do usuário.

Entrega em frota: `examples/mdm/`, detalhado em [06](06_permissoes_seguranca.md).
Verificação: `/status` lista a fonte sob **Setting sources**.

## Config: o menu como dado

`ConfigRow` (`claude-code.d.ts:1465`) é uma linha do `/config` como `$.config.list()` a
devolve — "o que o menu desenharia agora, **depois de todos os hooks `config.describe`**,
uma linha escondida deixada de fora":

| Campo | O que é |
|---|---|
| `key` | o id do painel para um built-in (`theme`, `verbose`, `autoCompact`), ou `<plugin>.<campo>` para um campo de `userConfig` de plugin |
| `label`, `description?` | o que o menu desenha |
| `kind` | `'boolean' \| 'choice' \| 'text' \| 'number'` |
| `value` | `boolean \| string \| number \| readonly string[]` |
| `options?` | os valores de uma linha `choice`, em ordem |
| `provider` | quem é dono da linha: o engine, ou o plugin |
| `isLocked` | **se uma fonte confiável (managed settings, política da organização) é dona do valor**, de modo que o menu o mostra e recusa mudança |

`isLocked` é a ponte entre os dois sistemas: settings gerenciados aparecem no menu como linha
travada, visível e inalterável — em vez de simplesmente sumirem.

## `config.set`: proveniência de três tipos

```ts
type ConfigOrigin =
  | { kind: 'composer' }                 // a pessoa, no menu ou /config key=value
  | { kind: 'bridge' }                   // um /config key=value que chegou pelo Remote Control
  | { kind: 'plugin'; name: string }     // $.config.set de um plugin
```
`claude-code.d.ts:1438`.

O comentário do `bridge` é o detalhe que vale o capítulo:

> Um `/config key=value` que chegou pela ponte de Remote Control (um telefone ou cliente web,
> ou um relay): **não atestavelmente a mão do dono**.

O harness modela "esta mudança veio de um canal que não prova quem é" como um tipo distinto,
e deixa a decisão para quem hooka. Um plugin de política pode recusar `bridge` e aceitar
`composer` sem nenhuma outra informação.

E: "`$.config.set` de um plugin — **os hooks daquele plugin não veem**". Mesma regra
anti-recursão dos subagentes ([14](14_subagentes_skills_comandos.md)).

`ConfigSetInput` traz `key`, `value`, `previous`, `provider` e `origin`; **só `value` é
reescrevível** — `next({ ...e, value })` "clampa ou substitui, mantido ao `kind` da linha".
O resultado é `{ value }` ou `{ deny: reason }`, e "o menu mostra a razão do deny ao lado da
linha".

## `config.describe`

Roda antes de a linha ser listada, e é o que permite a um plugin esconder uma linha, mudar
label/description, ou restringir `options`. `ConfigDescribeResult` é
`Omit<ConfigDescribeInput, 'key' | 'provider'>` (`claude-code.d.ts:1229`, análogo ao de
comando) — ou seja, tudo menos a identidade da linha e o dono dela pode ser redescrito.

É outro dos eventos que o `sec-default` empurra para além do tier do usuário, pelo mesmo
motivo de `tool.describe`: a descrição é o que a pessoa lê para decidir.

## Config de plugin

Um plugin declara campos `userConfig` no manifesto; eles viram linhas `<plugin>.<campo>` no
`/config`, com `kind` e `options` derivados da declaração. A partir daí é indistinguível de
uma linha built-in — o mesmo `config.set`, o mesmo `isLocked`, a mesma proveniência.

Note o contraste com as **opções** de um plugin (o segundo parâmetro de `register`): essas
são fixas por ativação e uma mudança recarrega o plugin ([08](08_plugins_e_mods.md)). Config
é para o que muda em runtime; options para o que não muda.

## Variáveis de ambiente

`$.env.get` / `$.env.set` são eventos como os outros, e o mod `telemetry` mostra o uso
canônico: ler cada switch **por nome literal, a cada chamada**, sem cachear
([10](10_mod_telemetry.md)).

O `CHANGELOG` é a melhor fonte para o inventário de variáveis (`CLAUDE_CODE_*`,
`ANTHROPIC_*`, `OTEL_*`, `DISABLE_*`) — ver [17](17_evolucao_changelog.md).

## Ver também

- [06](06_permissoes_seguranca.md) — as chaves de permissão e sandbox
- [11](11_mod_sec_default.md) — por que `settings.read` é protegido
- [17](17_evolucao_changelog.md) — como a superfície de settings cresceu
