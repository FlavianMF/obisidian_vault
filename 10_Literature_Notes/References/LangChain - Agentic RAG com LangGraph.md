---
title: "Build a custom RAG agent with LangGraph"
type: article
tags: [rag, agentic-rag, langgraph, tutorial]
created: 2026-10-22
provenance: obsidian_vault
authors: LangChain
year: 2025
source: https://docs.langchain.com/oss/python/langgraph/agentic-rag
verified: 2026-10-22 via leitura da página com WebFetch (subagente de pesquisa)
confidence: low
seen_in: [obsidian_vault]
---

# Build a custom RAG agent with LangGraph

Documentação · LangChain · 2025 · <https://docs.langchain.com/oss/python/langgraph/agentic-rag>

## 📝 Resumo

- O grafo deixa o modelo decidir se chama a ferramenta retriever ou se responde direto.
- Um nó classifica os documentos em sim ou não, com saída estruturada.
- Documento irrelevante leva ao nó rewrite_question, que tenta de novo. Documento relevante leva ao nó generate_answer.
- O URL antigo em langchain-ai.github.io só redireciona.

## Confiabilidade

Doc sem data; o ano é estimativa. É uma implementação simplificada de CRAG e Self-RAG. A descrição lida não mostra teto de tentativas: em produção, ponha um.

## 🔗 Conexões

- [[Agentic RAG]]
- [[Estudo - Agentic RAG no Second Brain]]
