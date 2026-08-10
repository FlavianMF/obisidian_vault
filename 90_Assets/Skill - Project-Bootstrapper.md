---
title: Skill: Project-Bootstrapper
type: pattern
tags: [agentic-ai, automation, dev-environment]
created: 2026-05-21
provenance: manual
---

# Skill: Project-Bootstrapper

## Comportamento
Automação do setup de novos ambientes para garantir consistência.

## Regras
1. **Setup de Estrutura**: Criar `docs/`, `src/`, `docker/` automaticamente.
2. **Template de Prompt**: Copiar `90_Assets/Template_Project_Prompt.md` para `docs/PROMPT.md` do novo projeto.
3. **Versionamento Inicial**: `git init` e `git checkout -b feat/init-project`.
