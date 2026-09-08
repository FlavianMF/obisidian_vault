---
title: Persistência de sessão
type: project
tags: [opencode, sqlite, persistence, session]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

> Ver [[opencode]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Persistência de sessão

[← Índice](00_indice.md)

Duas camadas de storage coexistem no código-fonte, refletindo uma migração em andamento.

## Legado: storage JSON por arquivo

`packages/opencode/src/storage/storage.ts` — uma `Interface { read, write, update, remove, list }` chaveada por `key[]`, materializada como `<dir>/<key...>.json`, com `MIGRATIONS` versionadas que movem dados de um layout antigo por-projeto para um layout novo `project/<id>.json` + `session/<projectID>/<sessionID>.json`.

## Atual: SQLite via Drizzle

`packages/core/src/database/database.ts`, usando `@opencode-ai/effect-drizzle-sqlite`. Lógica de path do arquivo de DB padrão (trecho de fonte):

```ts
export function path() {
  if (Flag.OPENCODE_DB) {
    if (Flag.OPENCODE_DB === ":memory:" || isAbsolute(Flag.OPENCODE_DB)) return Flag.OPENCODE_DB
    return join(Global.Path.data, Flag.OPENCODE_DB)
  }
  ...
  return join(Global.Path.data, "opencode.db")   // padrão: ~/.local/share/opencode/opencode.db
}
```

PRAGMAs configuradas: journal mode WAL, `synchronous=NORMAL`, `busy_timeout=5000`, `foreign_keys=ON`.

**`OPENCODE_DB` é diretamente útil para harness/CI:** apontar para `:memory:` ou um path absoluto por-execução para isolar/sandboxar runs.

## Resume

Sessões persistem entre restarts. `opencode run --continue`/`-c` ou `--session <id>`/`-s`, mais `--fork` (fork antes de continuar, requer `--continue`/`--session`).

## Export/Import

- `opencode export <sessionID> --sanitize` (redige segredos)
- `opencode session list --format json`
- `opencode session delete <id>`
- Import a partir de arquivo JSON ou de uma URL de share
- `opencode db [query]` — comando de inspeção crua do DB

## Sharing

Docs: [opencode.ai/docs/share](https://opencode.ai/docs/share/). `/share` cria uma URL pública em `opncd.ai/s/<share-id>` e sincroniza o histórico com os servidores do próprio OpenCode (hospedado por terceiro, não self-hostable nesse fluxo); modos: `"manual"` (padrão), `"auto"`, `"disabled"` via chave de config `"share"`. `/unshare` apaga o dado remoto.

## Ver também

- [12_headless_sdk_api.md](12_headless_sdk_api.md) — flags de CLI de resume/fork/continue em contexto de automação
- [10_configuracao.md](10_configuracao.md) — chave `snapshot`
