---
title: gh: conta ativa errada dá 'Repository not found' ou 403 no push
type: trap
tags: [trap, residencia_cariri_projects]
created: 2026-10-30
provenance: residencia_cariri_projects
seen_in: [residencia_cariri_projects]
confidence: low
scope: global
verified: 2026-10-30 via candidato do agente em residencia_cariri_projects, não reproduzido na revisão
---

# gh: conta ativa errada dá 'Repository not found' ou 403 no push

## Contexto
Repos em contas diferentes (Flavian-FIT: residencia_cariri_projects; FlavianMF: dotfiles, vault). Push com a conta errada falha com 'Repository not found' (repo privado) ou 403. Rodar gh auth status antes; gh auth switch -u <conta>, push, restaurar a padrão.

## O que NÃO funcionou
- A preencher
