---
title: Skill: Ingestão de Notas de Literatura
type: pattern
tags: [agentic-ai, knowledge-management, citation, academic]
created: 2026-05-21
provenance: manual
---

# Skill: Ingestão de Notas de Literatura

Esta skill define o formato padrão para a criação de notas de literatura, garantindo rastreabilidade completa e acesso direto às fontes originais.

## 🤖 Comportamento Esperado
Ao identificar uma referência acadêmica relevante (em pesquisas ou discussões), o agente deve:

1.  **Criar Nota de Referência**: Criar um novo arquivo em `10_Literature_Notes/References/` com o nome `[[Sobrenome Ano]]`.
2.  **Seguir o Formato Padrão**: Utilizar a estrutura baseada no exemplo consolidado (`Behara & Naidoo 2026.md`):
    - **Frontmatter**: Incluir título, tipo (literature), tags e data de criação.
    - **Insights**: Lista resumida das descobertas principais.
    - **Conexões**: Links para notas permanentes relacionadas.
    - **Citação Completa**: No formato ABNT ou APA.
3.  **Link de Acesso Direto**: É **Obrigatório** incluir um campo ou seção "Acesso" com o link direto para o PDF (arXiv, ResearchGate) ou o DOI do artigo.
4.  **Linkagem no MOC**: Adicionar a nova nota à lista em `30_MOCs/Referências Bibliográficas.md`.

## 🖇️ Conexões
- [[Skill - Pesquisa Acadêmica Rigorosa]]
- [[90_Assets/Template_Referencia]]
- [[30_MOCs/Referências Bibliográficas]]

## Exemplo de Campo de Acesso
> **Acesso**: [Texto do Título](https://doi.org/xxxxx) ou [PDF via arXiv](https://arxiv.org/pdf/xxxx.pdf)
