---
title: Skill: Pesquisa Acadêmica Rigorosa
type: pattern
tags: [agentic-ai, research, academic, literature-review]
created: 2026-05-21
provenance: manual
---

# Skill: Pesquisa Acadêmica Rigorosa

Esta skill define o protocolo para agentes de IA realizarem pesquisas em bases de dados científicas e integrarem o estado-da-arte ao conhecimento do Flavian.

## 🤖 Comportamento Esperado
Sempre que o agente precisar validar uma teoria ou buscar uma nova solução tecnológica (especialmente para o [[Mestrado_ITA]]), deve seguir este fluxo:

1.  **Fontes Primárias**: Utilizar ferramentas de busca para consultar:
    - **Google Scholar**: Para artigos consolidados e contagem de citações.
    - **arXiv / Semantic Scholar**: Para as pesquisas mais recentes (SOTA).
    - **NASA Technical Reports (NTRS)**: Especificamente para Engenharia de Sistemas.
2.  **Filtro de Qualidade**: Priorizar artigos dos últimos 3-5 anos, a menos que sejam "seminal papers" (ex: publicações originais de SysML ou NASA SE Handbook).
3.  **Destilação (Workflow)**:
    - Criar uma nova nota em `10_Literature_Notes/References/` seguindo o padrão `[[Sobrenome Ano]]`.
    - Extrair: Problema, Metodologia, Principais Insights e Conexões com o Vault.
    - Adicionar a citação completa e links (DOI/URL).
4.  **Citação Proativa**: Nunca introduzir um conceito acadêmico novo sem linkar para a respectiva nota de literatura.

## 🖇️ Conexões
- [[30_MOCs/Referências Bibliográficas]]
- [[90_Assets/Template_Referencia]]
- [[00_META/Agent-Instruction]]

## Fontes
- Protocolo de Revisão Sistemática (PRISMA adaptado para Agentes).
