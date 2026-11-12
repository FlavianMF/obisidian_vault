---
title: "Frontmatter de SKILL.md com dois-pontos e aspas quebra o YAML"
type: permanent
created: 2026-11-10T14:04:44
moc: "Design de Interface com Agente"
tags: [yaml, skill, agent]
source_inbox: "e310617f-frontmatter-de-skill-md-com-dois-pontos-e-aspas-quebra-o-yam.md"
tier: "L2"
score: 0.73
---

# Frontmatter de SKILL.md com dois-pontos e aspas quebra o YAML

description ou argument-hint com 'ex.: ' ou aspas e < > sem quote viram YAML inválido e a skill não carrega. Envolva o valor em aspas simples e valide com yaml.safe_load num teste.

# Contexto

O candidato identificou um problema no frontmatter de um arquivo `SKILL.md`. O uso de dois-pontos (`:`) e aspas (`'` ou `"`) em certas partes do frontmatter resulta em um YAML inválido, impedindo que a skill não carregue corretamente.

# Detalhes

- **Arquivo**: SKILL.md
- **Problema**: Descrição ou argument-hint contendo 'ex.: ' ou aspas e `< >` sem quote.
- **Efeito**: YAML inválido, impedindo o carregamento da skill.
- **Solução sugerida**: Envolva o valor em aspas simples e valide com `yaml.safe_load` num teste.

# Próximos passos

1. Modificar o frontmatter do arquivo `SKILL.md`, envelopando valores problemáticos em aspas simples.
2. Adicionar um teste unitário para validar o carregamento da skill após a modificação.
3. Revisar e testar a skill novamente para garantir que o problema foi resolvido.

## Conexões
- [[Design de Interface com Agente]]
