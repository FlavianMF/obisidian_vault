---
title: Skill: Graph-Gardener
type: pattern
tags: [agentic-ai, obsidian, knowledge-graph]
created: 2026-05-21
provenance: manual
---

# Skill: Graph-Gardener

## Comportamento
Manutenção ativa da densidade de rede do vault.

## Regras
1. **Linkagem Inline**: Sempre que citar um conceito técnico (ex: Docker, MBSE, SysML), envolva em `[[wikilinks]]`.
2. **First Mention Rule**: Linkar apenas a primeira menção por nota.
3. **Curadoria de MOC**: Ao criar uma nota nova, o agente deve verificar se ela precisa ser adicionada a algum MOC e executar a inserção (ou sugerir via `/moc-update`).
