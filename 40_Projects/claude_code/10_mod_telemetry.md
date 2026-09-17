---
title: mods/telemetry dissecado — estender o $
type: project
tags: [claude-code, plugins, telemetry, privacy, api-design]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# `mods/telemetry` dissecado — estender o `$` em 45 linhas

[← Índice](00_indice.md)

81 arquivos, mas o hook é **um só**. Este mod existe para demonstrar (e para usar de
verdade) o mecanismo de extensão do `$`: um passo de `engine.create` que adiciona um
substantivo novo.

## O hook inteiro

```ts
export function register(on: On) {
  on('engine.create', async ($, e, next) => {
    const beneath = await next(e)

    const telemetry: EngineInterface['telemetry'] = telemetryOf({
      authorize: () => beneath.session.authorize(),
      id:        () => beneath.session.id(),
      model:     () => beneath.session.model(),
      environment: async () => ({ userType: await beneath.env.get('USER_TYPE'), /* ... */ }),
      fetch:     (url, init) => beneath.http.fetch(url, init),
    })

    return { ...beneath, telemetry }
  })
}
```
`mods/telemetry/hooks/register.ts`.

Quatro fatos de arquitetura cabem aí:

1. **`next(e)` resolve para o `$` construído abaixo.** O fold sobe: cada passo recebe o que
   os passos internos montaram e devolve o que os externos vão receber
   (`NextResult<'engine.create'> = EngineInterfaceBuilt`, `claude-code.d.ts:4340`).
2. **`{ ...beneath, telemetry }` adiciona sem substituir.** O README do mod diz por quê:
   *"o substantivo é adicionado e nada abaixo é substituído"*. Substituir faria o passo
   falhar, nomeando os dois plugins (`claude-code.d.ts:3197-3200`).
3. **O substantivo novo é construído sobre os substantivos de baixo.** `$.telemetry` não
   tem acesso privilegiado a nada: é `session.authorize` + `session.id` + `session.model` +
   `env.get` + `http.fetch`, e nada mais.
4. **Vira evento automaticamente.** Como `telemetry` está declarado em `EngineInterface`,
   seus métodos entram em `NounEventOf` (`claude-code.d.ts:4413`) — `on('telemetry.log', ...)`
   é um hook válido, e quem quiser auditar analytics não precisa de API nova.

## Como o contrato é publicado

```json
// .claude-plugin/plugin.json
{ "name": "telemetry", ..., "types": "./types/index.d.ts" }
```

O campo `"types"` aponta para o `.d.ts` que faz declaration merging em `EngineInterface`.
O README explica o papel dele: *"`types/index.d.ts` é o contrato do substantivo, a única
declaração de `$.telemetry` que os hooks deste mod, um mod chamando o substantivo e um teste
respondendo a ele leem"*. Uma declaração, três consumidores — e o comando `/plugin-types`
copia isso para `.claude/types/claude-code-plugins/<plugin>.d.ts` de quem depende
(`claude-code.d.ts:44-50`).

## A política de privacidade está no código, não num documento

Vale registrar porque é um exemplo concreto de como se implementa opt-out de verdade num
harness. Do README:

> Não manda nada onde os analytics do próprio CLI estão desligados: sob `DISABLE_TELEMETRY`,
> `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` ou `DO_NOT_TRACK`, em qualquer provider
> terceiro (Bedrock, Vertex, Foundry e afins), e num deployment com URL de OAuth própria.
> **Cada um é lido pelo `$.env` a cada chamada**, e a credencial é autorizada de novo logo
> antes de cada POST, para que uma sessão que desde então migrou para um provider terceiro
> ou um gateway em nuvem não mande mais nada.

Ou seja: nada é cacheado no boot. A decisão de enviar é recomputada por evento, a partir do
ambiente corrente. É mais caro e é o certo.

As variáveis lidas, todas por nome literal via `beneath.env.get`: `USER_TYPE`,
`DISABLE_TELEMETRY`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, `DO_NOT_TRACK`,
`CLAUDE_CODE_CUSTOM_OAUTH_URL`, `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`,
`CLAUDE_CODE_USE_FOUNDRY`, `CLAUDE_CODE_USE_ANTHROPIC_AWS`,
`CLAUDE_CODE_USE_ANTHROPIC_GOOGLE_CLOUD`, `CLAUDE_CODE_USE_MANTLE`.

## Nada free-form entra numa linha

A validação é estrutural, não por sanitização:

> Um nome de evento e toda chave de propriedade é um token snake_case; um valor é um número
> finito, um booleano, ou um **Choice** (uma string nomeada junto com a lista de onde é
> escolhida), sob `log` e `mark` igualmente; `mark` aceita `ok`, `sad` ou `bad`, com `reason`
> obrigatório nos dois últimos e recusado no primeiro. Uma entrada que quebra uma regra é
> recusada antes de qualquer coisa ser enviada.

O tipo `Choice` é a ideia interessante: em vez de aceitar uma string qualquer, a chamada
carrega o valor **e o conjunto de onde ele veio**. É assim que o `diff` grava:

```ts
record.mark(FEATURES.tabSwitch, { kind: 'ok', props: { tab: { value: tab, of: Record.TABS } } })
```

Um campo livre nunca vira dado de analytics por acidente — e o esquema da tabela é derivável
do código.

## API de envio: uma linha, uma tentativa, nada em lote

`$.telemetry.log({ event, props })` manda `tengu_plugin_<event>`;
`$.telemetry.mark({ feature, kind, reason?, props? })` manda `tengu_feature_<kind>` com
`feature_name`. Cada chamada é **um POST**, com a credencial da própria sessão
(`$.session.authorize()`, resolvida a cada chamada), uma tentativa, nada em lote. Sessão sem
credencial first-party, ou ingest que recusa, **rejeita a promise de quem chamou** — o
plugin sabe que não foi.

## Onde ele roda (e por que isso importa para quem lê o repo)

> Este plugin é assentado pelo próprio CLI, em builds internos cujos analytics estão ligados,
> e em nenhum outro lugar: `session.authorize` só existe lá. **Não é feito para ser instalado
> nem carregado com `--plugin-dir`**; a pasta tem um manifesto para ler como todo plugin, não
> para poder rodar sozinha.

Leitura para esta pesquisa: `mods/telemetry` é útil como **exemplo canônico de extensão do
`$`**, e não como ferramenta reutilizável.

## Ver também

- [02](02_modelo_engine_hooks.md) — o fold `engine.create`
- [09](09_mod_diff.md) — o consumidor real de `$.telemetry`
- [17](17_evolucao_changelog.md) — o outro canal de telemetria, OpenTelemetry
