---
title: "Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity"
type: article
tags: [rag, agentic-rag, routing, retrieval]
created: 2026-10-22
provenance: obsidian_vault
authors: Jeong, Baek, Cho, Hwang, Park
year: 2024
source: https://arxiv.org/abs/2403.14403
verified: 2026-10-22 via leitura do abstract com WebFetch (subagente de pesquisa)
confidence: low
seen_in: [obsidian_vault]
---

# Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity

Paper · Jeong, Baek, Cho, Hwang, Park · 2024 · <https://arxiv.org/abs/2403.14403>

## 📝 Resumo

- Um LM pequeno classifica a complexidade da pergunta.
- A classe escolhe a estratégia: sem retrieval, retrieval de um passo ou retrieval iterativo.
- Evita gastar compute em perguntas simples e melhora as perguntas de vários passos.

## Confiabilidade

Paper do NAACL 2024. É o argumento central contra rodar o loop agêntico em toda pergunta.

## 🔗 Conexões

- [[Agentic RAG]]
- [[Estudo - Agentic RAG no Second Brain]]
