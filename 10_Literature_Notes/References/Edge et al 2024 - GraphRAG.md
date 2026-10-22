---
title: "From Local to Global: A Graph RAG Approach to Query-Focused Summarization"
type: article
tags: [rag, graphrag, knowledge-graph, retrieval]
created: 2026-10-22
provenance: obsidian_vault
authors: Edge, Trinh, Cheng, Bradley, Chao, Mody, Truitt, Metropolitansky, Ness, Larson
year: 2024
source: https://arxiv.org/abs/2404.16130
verified: 2026-10-22 via leitura do abstract com WebFetch (subagente de pesquisa)
confidence: low
seen_in: [obsidian_vault]
---

# From Local to Global: A Graph RAG Approach to Query-Focused Summarization

Paper · Edge, Trinh, Cheng, Bradley, Chao, Mody, Truitt, Metropolitansky, Ness, Larson · 2024 · <https://arxiv.org/abs/2404.16130>

## 📝 Resumo

- O RAG comum falha em perguntas globais, como "quais são os temas principais do corpus?".
- Constrói um índice em dois estágios: grafo de entidades e resumos de comunidades.
- Combina respostas parciais por comunidade. Em corpora de cerca de 1 milhão de tokens, ganha em abrangência e diversidade.

## Confiabilidade

Trabalho da Microsoft Research. O índice usa LLM para extrair entidades, o que custa caro em corpus que muda.

## 🔗 Conexões

- [[Agentic RAG]]
- [[Estudo - Agentic RAG no Second Brain]]
