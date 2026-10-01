---
title: "Claude Plugin CLI reescreve o settings.json symlinkado do repo"
type: trap
tags: [claude-code, plugins, dotfiles, settings]
created: 2026-09-30
provenance: dotfiles
seen_in: [dotfiles]
confidence: medium
scope: global
verified: 2026-09-30 via git diff claude/settings.json depois de marketplace add / plugin install do ecc@ecc
---

# Claude Plugin CLI reescreve o settings.json symlinkado do repo

Quando `~/.claude/settings.json` é symlink para um arquivo versionado (dotfiles), os
comandos de plugin do [[claude-code]] escrevem **direto no arquivo do repo**:

- `claude plugin marketplace add <repo>` regrava `extraKnownMarketplaces` e **apaga
  `autoUpdate: false`** da entrada já declarada. O pin some sem aviso.
- `claude plugin install <id>` grava `enabledPlugins[id] = true`, mesmo que o arquivo
  declarasse `false` (plugin "instalado e desligado").
- `claude plugin configure --values-stdin` grava `pluginConfigs` no mesmo arquivo. Esse é
  bem-vindo, porque deixa a config declarativa.

## Como lidar

- Depois de reconciliar plugins num script de install: devolver `autoUpdate: false` com
  `jq '.extraKnownMarketplaces |= with_entries(.value.autoUpdate = false)'` e escrever
  com `cat tmp > arquivo`, para preservar o symlink.
- Para plugin declarado `false`: rodar `claude plugin disable <id> -s user` logo após o
  install.
- Sempre revisar `git diff` do settings depois de mexer em plugin.

## 🔗 Conexões

- [[ECC - Adotar Ideias, Não o Runtime]]: onde apareceu (plugin `ecc@ecc` por projeto).
- [[Uma Fonte de Regra, N Harnesses Compilados]]
