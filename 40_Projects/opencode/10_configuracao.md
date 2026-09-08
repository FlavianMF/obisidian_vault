---
title: Configuração
type: project
tags: [opencode, configuration, xdg]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

> Ver [[opencode]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Configuração

[← Índice](00_indice.md)

Docs: [opencode.ai/docs/config](https://opencode.ai/docs/config/)

## Formato

**JSON ou JSONC** (`opencode.json` / `opencode.jsonc`), mais um arquivo separado `tui.json`/`tui.jsonc` só para settings de TUI. Schemas JSON publicados em `https://opencode.ai/config.json` e `https://opencode.ai/tui.json` — apontável direto num validador de editor/automação.

## Ordem de resolução (configs fazem merge, não substituem)

```
remoto (.well-known/opencode)
  → global (~/.config/opencode/opencode.json)
  → OPENCODE_CONFIG (path via env)
  → raiz do projeto (opencode.json)
  → subpastas .opencode/
  → OPENCODE_CONFIG_CONTENT (env inline)
  → settings gerenciadas por OS (/etc/opencode/, /Library/Application Support/opencode/, %ProgramData%\opencode)
  → .mobileconfig de MDM macOS
```

## Chaves de topo

`model`, `small_model`, `provider`, `default_agent`, `subagent_depth`, `tools`, `permission`, `theme`, `keybinds` (tui.json), `shell`, `agent`, `command`, `attachment.image`, `formatter`, `lsp`, `mcp`, `plugin`, `instructions`, `share`, `snapshot`, `watcher.ignore`, `compaction`, `server`, `autoupdate`, `disabled_providers`/`enabled_providers`, `experimental.policies`.

## Substituição de variável

`{env:VAR}` e `{file:path}`. Overrides via env: `OPENCODE_CONFIG`, `OPENCODE_CONFIG_DIR`, `OPENCODE_CONFIG_CONTENT`, `OPENCODE_TUI_CONFIG`.

## XDG base dirs

Confirmado em `packages/core/src/global.ts`: opencode usa XDG base dirs — dados em `$XDG_DATA_HOME/opencode` (→ `~/.local/share/opencode` no Linux), config em `$XDG_CONFIG_HOME/opencode`, cache/state/tmp namespaced de forma similar — tudo sobrescrevível (`OPENCODE_CONFIG_DIR` para config).

## Exemplo — config de servidor

```json
{
  "server": {
    "port": 4096,
    "hostname": "0.0.0.0",
    "mdns": true,
    "mdnsDomain": "myproject.local",
    "cors": ["http://localhost:5173"]
  }
}
```

## Ver também

- [07_permissoes_seguranca.md](07_permissoes_seguranca.md) — chave `permission`
- [08_mcp.md](08_mcp.md) — chave `mcp`
- [13_multiagente_subagentes.md](13_multiagente_subagentes.md) — chave `agent`
- [12_headless_sdk_api.md](12_headless_sdk_api.md) — chave `server` no contexto de `opencode serve`
