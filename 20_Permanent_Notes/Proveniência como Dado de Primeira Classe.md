---
title: Proveniência como Dado de Primeira Classe
type: pattern
tags: [security, audit, agent-architecture, provenance, mbse]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

# Proveniência como Dado de Primeira Classe

Num sistema onde ações chegam de vários lados — a pessoa, o modelo, um plugin, um relay
remoto, um agente em background — **de onde veio** é tão parte da ação quanto *o que* ela é.
Trate como campo, escrito pelo sistema, não inferível e não falsificável.

O [[claude-code]] leva isso longe, e a densidade é o que impressiona:

| Campo | O que distingue |
|---|---|
| `next.origin` | `{ plugin, tier }` de quem levantou o dispatch. Escrito **só pelo host**, a partir do `MessagePort` de onde a chamada veio — nada que o plugin escreva chega aqui |
| `e.provider` (pinado) | de onde vem a *coisa* descrita (uma ferramenta, um agente, um comando) — eixo distinto de quem chama |
| `origin.kind === 'person'` | a pessoa apertou, versus um plugin fechou |
| `ConfigOrigin` | `composer` (a pessoa no menu) × `plugin` × **`bridge`** |
| `AgentInfo.spawnedBy` × `parentId` | **origem** (que plugin causou) × **hierarquia** (que loop gerou) |
| `ToolCallReserved.consent` | as palavras da própria pessoa no aperto que autorizou (`The user pressed "1: Yes" on ...`), que entram no contexto como turno humano |

O caso mais fino é o `bridge`, documentado assim:

> Um `/config key=value` que chegou pela ponte de Remote Control (um telefone ou cliente web,
> ou um relay): **não atestavelmente a mão do dono**.

O sistema não decide o que fazer com isso — ele **nomeia a incerteza** e deixa a política
decidir. Um hook pode recusar `bridge` e aceitar `composer` sem nenhuma outra informação.

O mesmo princípio aparece na política de sandbox: um comando digitado no prompt `!` do usuário
roda fora do sandbox mesmo em modo estrito, *"como digitar no seu próprio terminal"* — a
mesma string proposta pelo modelo não roda. **A proveniência é parte da política, não
metadado.**

E é persistida, não só aplicada: a transcrição em disco grava `permissionMode`,
`toolDenialKind`, `promptSource`, `origin`, `entrypoint`, `isSidechain`.

**Aplicação a MBSE / Capella** (o motivo de esta nota existir): todo elemento criado ou
modificado num modelo por uma LLM deveria carregar **quem pediu** — a pessoa, o modelo por
iniciativa própria, ou um agente de teste. Um modelo que a IA tocou sem esse registro é
difícil de auditar depois, e auditabilidade é exatamente o que um trabalho sobre IA em MBSE
precisa demonstrar empiricamente. É também o campo mais barato de acrescentar e o de maior
retorno.

Ver também: [[Autoridade por Assento na Cadeia de Hooks]].
