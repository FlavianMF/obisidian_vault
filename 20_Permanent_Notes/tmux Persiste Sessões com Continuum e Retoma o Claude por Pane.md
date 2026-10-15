---
title: "tmux persiste sessões com continuum e retoma o Claude por pane"
type: pattern
tags: [tmux, claude-code, dotfiles, resurrect, continuum]
created: 2026-10-15
provenance: dotfiles
seen_in: [dotfiles]
confidence: low
scope: global
verified: 2026-10-15 via kill-server + novo tmux restaurou sessões e relançou os claude
---

# tmux persiste sessões com continuum e retoma o Claude por pane

Objetivo: comportamento de nvim/VS Code. Fechou, abriu de novo, o estado voltou, sem
`save`/`restore` manual.

## Receita
- `tmux-plugins/tmux-continuum` sobre `tmux-resurrect`, em `~/.tmux.conf`:
  `@continuum-restore "on"`, `@continuum-save-interval "5"`,
  `@resurrect-capture-pane-contents "on"`,
  `@resurrect-processes "nvim yazi ssh btop claude"`.
- O restore automático só dispara quando o servidor sobe **vazio** (reboot, crash,
  `kill-server`). Fechar a janela do terminal **não** mata o tmux: as sessões seguem vivas e
  basta `tmux attach`. Não precisa de auto-attach no zsh para isso.
- Retomar o [[claude-code]] por pane: o Claude grava `~/.claude/sessions/<pid>.json` com
  `sessionId` e `kind` (`bg` para background). Um hook
  `@resurrect-hook-post-save-layout` recebe o caminho do arquivo de save, percorre os
  descendentes de cada `pane_pid`, acha o `<pid>.json` com `kind != bg` e reescreve o último
  campo da linha `pane` para `:claude --resume <sessionId>`.
- Esse hook roda **antes** do `ln -fs ... last` e do `files_differ`, então a edição entra no
  snapshot que vira o `last`.

## O que NÃO funcionou
- Nada falhou no teste final: `kill-server` seguido de `tmux new` restaurou todas as sessões
  e os `claude` voltaram. Duas ressalvas: o `post-save-all` não recebe o caminho do arquivo
  (só o `post-save-layout` recebe), e o hook não relança flags originais como
  `--dangerously-skip-permissions`, de propósito.
