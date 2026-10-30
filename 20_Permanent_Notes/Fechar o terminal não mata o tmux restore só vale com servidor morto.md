---
title: Fechar o terminal não mata o tmux: restore só vale com servidor morto
type: trap
tags: [trap, dotfiles]
created: 2026-10-30
provenance: dotfiles
seen_in: [dotfiles]
confidence: low
scope: global
verified: 2026-10-30 via candidato do agente em dotfiles, não reproduzido na revisão
---

# Fechar o terminal não mata o tmux: restore só vale com servidor morto

## Contexto
Auto-restore do continuum só dispara em servidor vazio (reboot/crash/kill-server). Terminal fechado deixa as sessões vivas; basta tmux attach.

## O que NÃO funcionou
- A preencher
