---
title: Autoridade por Assento na Cadeia de Hooks
type: pattern
tags: [security, agent-architecture, plugin-api, policy, harness]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

# Autoridade por Assento na Cadeia de Hooks

Quando todo plugin pode enganchar todo evento ([[Toda Chamada na API é um Evento Interceptável]]),
a pergunta de segurança deixa de ser *"o que este plugin pode fazer?"* e passa a ser
**"onde este plugin senta?"**.

No [[claude-code]] a cadeia tem cinco tiers, do mais externo (mais autoridade) ao mais interno:

```
prepend  →  user  →  append  →  builtin  →  core
```

`prepend` e `append` são os plugins gerenciados que um administrador lista; `user` é tudo que
a pessoa instala; `builtin` são os plugins embutidos no binário; `core` é o engine.
Hooks do mesmo evento aninham nessa ordem **e em nenhuma outra**.

A primitiva que dá poder é `next.to(e, tier)` — continuar o dispatch pulando elos — e ela é
**restrita por construção**: `prepend` pode nomear `append`, `builtin` ou `core`; `append` só
`core`; **nunca se pula um tier de mais autoridade**. Um plugin do tier `user` não consegue
pular o da organização nem que queira, e os elos pulados ficam no `trace`.

**O caso de uso que prova o padrão** é o mod `sec-default`: 33 linhas, três movimentos
(`next.to(e, 'append')`, `{ deny }`, `next(e)`) e **nenhuma política própria**. Ele existe
porque a API de hooks tornaria alcançáveis controles organizacionais que antes não eram
(hooks clássicos, CLAUDE.md gerenciado, settings, allowlist de MCP); em vez de restringir a
API, escreveram um plugin que restaura o invariante — assentado por fora de todos.

E o fecho do argumento: *"é uma pasta de plugin como qualquer outra, mas o único movimento que
importa nela, `next.to`, é recusado fora de um tier gerenciado, então carregá-lo com
`--plugin-dir` assenta um plugin que só sabe passar"*. **A autoridade não está no código —
está no assento.**

**Como aplicar:** se o harness tem mais de um princípio de autoridade (organização × usuário,
projeto × sessão), modele isso como ordem na cadeia, não como lista de permissões por plugin.
Duas regras bastam: ordem determinística de aninhamento, e pulo de elo só para dentro.

Contraste: [[opencode]] não tem camada equivalente — a resolução é "a última regra que casa
vence", sem noção de autoridade de quem escreveu a regra.
