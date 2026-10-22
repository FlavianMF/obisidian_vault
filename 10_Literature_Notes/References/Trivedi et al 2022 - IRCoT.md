---
title: "Interleaving Retrieval with Chain-of-Thought Reasoning for Knowledge-Intensive Multi-Step Questions"
type: article
tags: [rag, agentic-rag, multi-hop, retrieval]
created: 2026-10-22
provenance: obsidian_vault
authors: Trivedi, Balasubramanian, Khot, Sabharwal
year: 2022
source: https://arxiv.org/abs/2212.10509
verified: 2026-10-22 via leitura do abstract com WebFetch (subagente de pesquisa)
confidence: low
seen_in: [obsidian_vault]
---

# Interleaving Retrieval with Chain-of-Thought Reasoning for Knowledge-Intensive Multi-Step Questions

Paper · Trivedi, Balasubramanian, Khot, Sabharwal · 2022 · <https://arxiv.org/abs/2212.10509>

## 📝 Resumo

- Alterna recuperação e sentenças de chain-of-thought. O que recuperar depende do que o modelo já derivou.
- Com GPT-3, ganha até 21 pontos em retrieval e até 15 em QA em HotpotQA, 2WikiMultihopQA, MuSiQue e IIRC. A v1 diz 22 e 16.
- Limitação: uma chamada de LLM por sentença, o que aumenta o custo.

## Confiabilidade

Paper do ACL 2023. Os números variam entre versões: cite a versão que você abriu.

## 🔗 Conexões

- [[Agentic RAG]]
- [[Estudo - Agentic RAG no Second Brain]]
