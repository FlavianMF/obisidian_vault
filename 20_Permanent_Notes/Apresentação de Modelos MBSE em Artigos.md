---
title: Apresentação de Modelos MBSE em Artigos
type: pattern
tags: [MBSE, SysML, academic-writing, systems-engineering, modeling]
created: 2026-05-21
provenance: manual
---

# 📐 Apresentação de Modelos MBSE em Artigos

A apresentação de modelos de [[MBSE]] e [[SysML]] em publicações científicas exige rigor visual e rastreabilidade para não ser reduzida a um simples "diagram dump".

## 🚀 Padrões de Excelência (SOTA 2025)

1.  **Transição para SysML v2**: Priorize o uso de [[SysML|SysML v2]]. Utilize a **Dual Representation**: gráficos para arquitetura de alto nível e trechos de texto (**KerML**) para lógica precisa e restrições.
2.  **Gráficos Vetoriais**: Nunca use JPEGs. Exporte diagramas como **PDF, EPS ou SVG**. O revisor deve conseguir dar zoom sem perda de qualidade.
3.  **Frames de Diagrama**: Todo diagrama deve ter o frame padrão (`bdd`, `ibd`, `act`, `stm`) com cabeçalho indicando o tipo de elemento e nome.
4.  **Elisão e Visualizações (Viewpoints)**: Não tente colocar o modelo completo em uma figura. Crie visualizações específicas (ex: "Safety View") e oculte detalhes irrelevantes para o argumento atual.
5.  **Single Source of Truth**: Declare explicitamente que o modelo é a fonte autoritativa de todos os dados, tabelas e requisitos apresentados no texto.

## 🏗️ Organização pelos "4 Pilares"
Ao descrever o sistema, organize a seção de métodos em:
- **Requirements**: Formalização de requisitos textuais em elementos de modelo.
- **Structure**: Hierarquia e conexões (BDD/IBD).
- **Behavior**: Funções e estados (Activity/State/Sequence).
- **Parametrics**: Restrições matemáticas vinculadas a solvers externos (ex: MATLAB/Python), demonstrando o [[Digital Twin|Digital Thread]].

## 🛠️ Validação e Reprodutibilidade
- **V&V Evidence**: Inclua evidências de que o modelo foi validado (simulação ou checking).
- **Repositório do Modelo**: Forneça o link (DOI) para os arquivos brutos do modelo (`.sysml`, `.xmi`) em um repositório como Zenodo.

## 🖇️ Conexões
- [[Visualização Científica e Resumos Gráficos]]
- [[Reproduzibilidade e Open Science (2025)]]
- [[Capella MBSE]]
- [[Mestrado_ITA]]
