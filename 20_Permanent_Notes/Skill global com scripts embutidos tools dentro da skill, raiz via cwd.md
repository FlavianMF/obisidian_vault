---
title: Skill global com scripts embutidos: tools/ dentro da skill, raiz via cwd
type: pattern
tags: [pattern, residencia_cariri_projects]
created: 2026-10-30
provenance: residencia_cariri_projects
seen_in: [residencia_cariri_projects]
confidence: low
scope: global
verified: 2026-10-30 via candidato do agente em residencia_cariri_projects, não reproduzido na revisão
---

# Skill global com scripts embutidos: tools/ dentro da skill, raiz via cwd

## Contexto
Para a skill funcionar fora do repo de origem, copiar os scripts para <skill>/tools/ (dotfiles agents/skills + link_shared_skill no install.sh) e trocar caminhos fixos '../..' por process.cwd(); comandos rodam da raiz do repo alvo. Validar com diff da saída entre a cópia e o original.

## O que NÃO funcionou
- A preencher
