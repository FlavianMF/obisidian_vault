---
title: Permissões e segurança
type: project
tags: [opencode, permissions, security, approval-gate]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

> Ver [[opencode]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Permissões e segurança

[← Índice](00_indice.md)

Docs: [opencode.ai/docs/permissions](https://opencode.ai/docs/permissions/) · Fonte: `packages/opencode/src/permission/index.ts`, `packages/opencode/src/permission/evaluate.ts`

## Modelo allow/ask/deny

Ações passíveis de gate: `read, edit, glob, grep, bash, task, skill, lsp, question, webfetch, websearch, external_directory, doom_loop`. Regras resolvem para `"allow" | "ask" | "deny"`.

Config global por tool:
```json
{ "permission": { "*": "ask", "bash": "allow", "edit": "deny" } }
```

Config por padrão dentro de uma tool:
```json
{ "permission": { "bash": { "*": "ask", "git *": "allow", "rm *": "deny" } } }
```

Matching usa wildcards estilo glob (`*`/`?`); **a última regra que der match vence** (`Wildcard.match`, `findLast`).

## Mecanismo de runtime — fila de request/deferred

`permission/index.ts`: fluxo assíncrono de request/deferred. `Service.ask()` cria um `Deferred`, publica um evento `PermissionV1.Event.Asked`, e bloqueia a execução da tool até `reply()` (`once` | `always` | `reject`) resolver.

**Isso é exatamente o mecanismo que um harness externo que dirige a API HTTP precisa "encaixar":**
- `GET /api/permission/request` (ou v1: `GET /permission`)
- `POST /session/{id}/permission/{requestID}/reply` (ou v2: `/api/session/{sessionID}/permission/{requestID}/reply`)

## Flags de bypass (CLI)

Confirmadas em `packages/opencode/src/cli/cmd/run.ts`:

```
--auto                          # auto-aprova tudo que não é explicitamente "deny" (docs chamam de "dangerous!")
--yolo                          # flag oculta
--dangerously-skip-permissions  # flag oculta
```

Regras `"deny"` explícitas são sempre aplicadas mesmo com `--auto`.

> **Nota de proveniência:** durante essa pesquisa, o WebFetch da doc oficial de CLI (`opencode.ai/docs/cli`) foi automaticamente sinalizado por conter o padrão de texto `--dangerously-skip-permissions`, e o output do agente veio com tags neutralizadas por precaução. Confirmado: é uma flag real, documentada oficialmente pelo próprio opencode — não uma tentativa de injeção de prompt encontrada na página. Registro isso aqui só para deixar claro que o "alerta" era sobre o *nome da flag*, não sobre conteúdo malicioso da doc.

## Camada complementar: `experimental.policies`

Docs: [opencode.ai/docs/policies](https://opencode.ai/docs/policies/). Configurável em `experimental.policies` no config — atualmente só controla `provider.use` (allow/deny de um provider de LLM por ID), com config global sobrepondo config de projeto (um repo não pode reabilitar um provider bloqueado globalmente). Eixo diferente de `permission` (acesso a recurso/tool-call vs. bloqueio de provider inteiro) — relevante se um harness precisar impor "só provider X" como política organizacional, independente de config de repositório individual.

## Ver também

- [09_plugins.md](09_plugins.md) — hook `permission.ask` permite política de aprovação programática (em código), alternativa/complemento às regras JSON acima
- [03_agent_loop.md](03_agent_loop.md) — onde no loop de execução o gate de permissão é checado
- [15_implicacoes_harness.md](15_implicacoes_harness.md) — padrão "permission-as-deferred-promise" como candidato a reaproveitar num harness próprio
