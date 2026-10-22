---
title: "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection"
type: article
tags: [rag, agentic-rag, self-reflection, retrieval]
created: 2026-10-22
provenance: obsidian_vault
authors: Asai, Wu, Wang, Sil, Hajishirzi
year: 2023
source: https://arxiv.org/abs/2310.11511
verified: 2026-10-22 via leitura do abstract com WebFetch (subagente de pesquisa)
confidence: low
seen_in: [obsidian_vault]
---

# Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection

Paper · Asai, Wu, Wang, Sil, Hajishirzi · 2023 · <https://arxiv.org/abs/2310.11511>

## 📝 Resumo

- Um único LM decide quando recuperar e critica as passagens e a própria saída com reflection tokens.
- O comportamento é controlável na inferência.
- Modelos de 7B e 13B superam ChatGPT e Llama2-chat com RAG em QA aberto, raciocínio e verificação de fatos.
- Melhora a factualidade e a acurácia de citação.

## Confiabilidade

Paper com revisão por pares (ICLR 2024). Exige treinar o modelo: num harness pronto, só a ideia de reflexão se transfere, por prompt.

## 🔗 Conexões

- [[Agentic RAG]]
- [[Estudo - Agentic RAG no Second Brain]]
