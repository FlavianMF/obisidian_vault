---
title: "agents/skills/ é ignorado pelo .gitignore (skills/)"
type: permanent
created: 2026-11-10T14:08:10
moc: "Design de Interface com Agente"
tags: [git, agent, skills]
source_inbox: "3ee2f82f-agents-skills-e-ignorado-pelo-gitignore-skills.md"
tier: "L2"
score: 0.766
---

# agents/skills/ é ignorado pelo .gitignore (skills/)

Skill nova em agents/skills/<nome> exige git add -f, como as já rastreadas. Registro de skills compartilhadas fica só no install.sh (link_shared_skill + lista de backup).

# agents/skills/ é ignorado pelo .gitignore (skills/)

## Contexto
A skill nova em `agents/skills/<nome>` não está sendo rastreada pelo `.gitignore`, o que requer manualmente o uso de `git add -f` para adicionar a nova skill ao repositório.

## Detalhes
- **Problema**: As novas skills adicionadas em `agents/skills/<nome>` não são automaticamente rastreadas pelo `.gitignore`.
- **Impacto**: Isso pode levar a erros de versionamento e dificuldade na manutenção do repositório.
- **Solução Proposta**: Adicionar `skills/` ao `.gitignore` para evitar o uso de `git add -f`.

## Próximos Passos
1. Atualizar o `.gitignore` para incluir `skills/`.
2. Verificar se há outras pastas que também devem ser ignoradas.
3. Realizar um commit dos arquivos modificados no `.gitignore`.

## Conexões
- [[Design de Interface com Agente]]
