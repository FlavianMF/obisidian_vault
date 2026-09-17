---
title: mods/sec-default dissecado — segurança como posição na cadeia
type: project
tags: [claude-code, security, plugins, policy, tiers]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# `mods/sec-default` dissecado — segurança como posição na cadeia

[← Índice](00_indice.md)

60 arquivos, 33 linhas de `register`. É o mod mais curto e o mais importante
conceitualmente: ele mostra que, neste desenho, **segurança é um problema de assento**, não
de lista de permissões.

## O problema que ele resolve

Do README, e vale ler devagar:

> Function hooks dão a todo plugin uma palavra em todo evento, em ordem de cadeia, e os
> plugins que uma pessoa instala sentam no tier `user`, abaixo do tier `prepend` da
> organização e acima do `append` dela. **Parte do que uma organização configura hoje (seus
> hooks clássicos, seu CLAUDE.md gerenciado e suas regras, seus settings, sua allowlist de
> MCP) nunca esteve ao alcance de uma pessoa antes das function hooks**; assentado mais
> externamente, este plugin mantém exatamente essas coisas fora do alcance do tier `user` e
> não acrescenta política nenhuma própria.

Ou seja: a API nova de hooks é tão poderosa que **abriria um buraco de segurança** em
controles que já existiam. Em vez de restringir a API, a Anthropic escreveu um plugin que
restaura o invariante. Isso só é possível porque a ordem da cadeia é uma garantia dura.

## Três movimentos e nada mais

```ts
next.to(e, 'append')        // continua além do tier user
{ deny: ... }               // recusa um chamador do tier user, pelo nome
next(e)                     // passa
```

Nenhum outro. O mod não inspeciona conteúdo, não reescreve prompt, não bloqueia ferramenta
por nome. Ele só decide **até onde o evento desce**.

`next.to(e, tier)` é a primitiva central, e ela é privilegiada por construção
(`claude-code.d.ts:4278-4283`): `prepend` pode nomear `append`, `builtin` ou `core`;
`append` só `core`; nunca se pula um tier de mais autoridade. Um plugin do tier `user` não
consegue pular o da organização nem que queira.

## A tabela de decisões

`mods/sec-default/hooks/register.ts`, na íntegra do que registra:

| Evento(s) | Movimento | Por quê |
|---|---|---|
| `classic.*` | `next.to(e, 'append')` | Os hooks de settings da organização veem a entrada do engine, e a resposta deles é que vale |
| `prompt.section`, `prompt.context`, `skill.prompt`, `attribution.text` | `next.to(e, 'append')` | CLAUDE.md gerenciado, regras e skills de política chegam ao modelo **como escritos** |
| `settings.read` | `next.to(e, 'append')` | Nenhum hook de usuário reescreve o que qualquer chamador lê como settings — inclusive as leituras de política deste próprio mod |
| `tool.describe`, `command.describe`, `agent.offer`, `agent.spawn` | `pastUsers(e, next)` | Se o `e.provider.tier` do *sujeito* é `prepend`/`append`, pula o tier user; sujeito de `user`/`builtin`/`core` passa normal |
| `tool.register` | condicional | Chamador `prepend`/`append` pula; chamador `user` é **recusado pelo nome** enquanto os managed settings tiverem `allowedMcpServers` (definido, mesmo vazio); senão passa |
| `tool.list` | reconciliação | As ferramentas dos servidores MCP gerenciados são listadas **como os tiers da organização as listaram**; todo o resto como o tier user deixou |
| todo o resto | passa | `prompt.submit`, `turn.*`, `tool.call`, `tool.check`, `command.run`, `session.*`, `ui.*`, `fs.*`, `http.fetch`, `process.run`, `store.*`, `clock.*`, `model.*`, `mcp.call`, `audio.*`, `agent.list`, `engine.create` |

A última linha é tão importante quanto as outras: o mod declara explicitamente o que **não**
protege. `prompt.submit` continua aberto ao usuário — "uma pessoa mantém `prompt.submit` e o
contexto aditivo dele". `tool.call` e `tool.check` também. A política organizacional cobre
*o que a organização configura*, não *o que a pessoa faz*.

## Os dois idiomas de decisão

### Proveniência pinada, não inferida

> A proveniência de um sujeito é o `e.provider` **pinado** do evento.

Para `tool.describe` e afins, o que importa não é quem chamou, é de onde vem a *coisa*
descrita. Esse campo é pinado (não reescrevível) e vem do host. Já para `tool.register` o que
importa é quem chama, e aí a fonte é `next.origin.tier` — também escrito só pelo host, a
partir do `MessagePort` de onde a chamada veio ([02](02_modelo_engine_hooks.md)).

Dois eixos distintos, dois campos distintos, nenhum deles falsificável por plugin.

### Fail closed

> Política é lida por `$.settings.read({ source: "policy" })`, uma leitura servindo uma
> rajada; **ambos falham fechado**, então uma política ilegível conta como política em vigor.

O memo é `Policy.createPolicyMemo(Policy.POLICY_MEMO_MS)` — cache curto para não reler o
disco a cada evento de uma rajada, sem virar cache de boot.

## `tool.list`: reconciliar duas listagens

O caso mais sutil do mod:

```ts
on('tool.list', async ($, e, next) =>
  Policy.managedToolsRestored(
    await readPolicy(() => $.settings.read(Policy.SOURCE)).catch(() => undefined),
    await next.to(e, 'append'),   // a listagem sem o tier user
    await next(e),                // a listagem com o tier user
  ),
)
```

Ele roda a cadeia **duas vezes** — uma pulando o tier `user`, outra normal — e reconcilia:
ferramentas dos servidores MCP gerenciados vêm da primeira, todo o resto da segunda. Se não
houver política para ler, ou se qualquer uma das listagens recusar, "a listagem da
organização vale inteira".

Isso mostra uma capacidade do modelo que não é óbvia: `next` pode ser chamado mais de uma
vez, e `next.to` dá uma *visão contrafactual* da cadeia ("o que seria se o tier user não
existisse?").

## O assento

> O CLI o assenta primeiro no tier `prepend` onde quer que módulos de hooks carreguem, numa
> máquina com managed settings ou para uma organização Team ou Enterprise, **a não ser que**
> os managed settings definam `prependPlugins`: aí aquela lista é o tier prepend inteiro, e a
> organização nomeia `sec-default@builtin` nela na posição que quiser — por exemplo
> `"prependPlugins": ["acme-guard@acme-tools", "sec-default@builtin"]` — ou o deixa de fora.

E o fecho do argumento:

> É uma pasta de plugin como qualquer outra, mas o único movimento que importa nela,
> `next.to`, é recusado fora de um tier gerenciado, então carregá-lo com `--plugin-dir`
> assenta um plugin que só sabe passar.

O mod é inofensivo fora do lugar dele. A autoridade **não está no código** — está no assento.
Esse é o resumo do capítulo.

## Ver também

- [02](02_modelo_engine_hooks.md) — os cinco tiers e `next.to`
- [06](06_permissoes_seguranca.md) — as outras camadas de política
- [15](15_config_settings.md) — managed settings e MDM
