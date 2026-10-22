---
title: "Corrective Retrieval Augmented Generation"
type: article
tags: [rag, agentic-rag, retrieval, evaluation]
created: 2026-10-22
provenance: obsidian_vault
authors: Yan, Gu, Zhu, Ling
year: 2024
source: https://arxiv.org/abs/2401.15884
verified: 2026-10-22 via leitura do abstract com WebFetch (subagente de pesquisa)
confidence: low
seen_in: [obsidian_vault]
---

# Corrective Retrieval Augmented Generation

Paper · Yan, Gu, Zhu, Ling · 2024 · <https://arxiv.org/abs/2401.15884>

## 📝 Resumo

- Um avaliador leve atribui uma confiança à recuperação. A confiança dispara a ação: usar, corrigir ou descartar.
- Se o corpus estático falha, o método expande a busca com a web.
- O passo decompose-then-recompose filtra o conteúdo irrelevante dos documentos.
- É plug-and-play sobre outros métodos de RAG.

## Confiabilidade

A ideia de avaliar antes de usar se aplica sem treino. O risco é o avaliador fraco: ele aprova contexto ruim ou rejeita contexto bom.

## 🔗 Conexões

- [[Agentic RAG]]
- [[Estudo - Agentic RAG no Second Brain]]
