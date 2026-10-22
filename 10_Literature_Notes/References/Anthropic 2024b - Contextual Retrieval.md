---
title: "Introducing Contextual Retrieval"
type: article
tags: [rag, retrieval, bm25, reranking, anthropic]
created: 2026-10-22
provenance: obsidian_vault
authors: Anthropic
year: 2024
source: https://www.anthropic.com/news/contextual-retrieval
verified: 2026-10-22 via leitura da página com WebFetch (subagente de pesquisa)
confidence: low
seen_in: [obsidian_vault]
---

# Introducing Contextual Retrieval

Post · Anthropic · 2024 · <https://www.anthropic.com/news/contextual-retrieval>

## 📝 Resumo

- Se a base tem menos de 200 mil tokens (cerca de 500 páginas), ponha tudo no prompt com prompt caching.
- Acrescente contexto a cada chunk antes do embedding e antes do BM25.
- Falha no top-20: 5,7% sem nada, 3,7% com embeddings contextuais, 2,9% com BM25 contextual e 1,9% com reranking.
- Top-20 chunks foi melhor que top-10 e top-5.

## Confiabilidade

Fonte primária, publicada em 19/09/2024. Já citada pela RFC-001 (E3, E10).

## 🔗 Conexões

- [[Agentic RAG]]
- [[Estudo - Agentic RAG no Second Brain]]
