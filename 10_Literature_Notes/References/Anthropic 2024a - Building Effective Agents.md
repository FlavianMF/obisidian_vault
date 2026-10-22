---
title: "Building effective agents"
type: article
tags: [agentic-ai, agent-architecture, anthropic]
created: 2026-10-22
provenance: obsidian_vault
authors: Erik Schluntz e Barry Zhang (Anthropic)
year: 2024
source: https://www.anthropic.com/engineering/building-effective-agents
verified: 2026-10-22 via leitura da página com WebFetch (subagente de pesquisa)
confidence: low
seen_in: [obsidian_vault]
---

# Building effective agents

Post · Erik Schluntz e Barry Zhang (Anthropic) · 2024 · <https://www.anthropic.com/engineering/building-effective-agents>

## 📝 Resumo

- Separa workflows (caminho predefinido) de agentes (o LLM dirige o processo).
- Recomenda a solução mais simples. Agentes trocam latência e custo por desempenho e compõem erros.
- Padrões: prompt chaining, routing, parallelization, orchestrator-workers e evaluator-optimizer.
- O bloco básico é o "LLM aumentado": retrieval, ferramentas e memória.
- O design da ferramenta importa: caminhos absolutos eliminaram uma classe de erros.

## Confiabilidade

Fonte primária de engenharia, publicada em 19/12/2024.

## 🔗 Conexões

- [[Agentic RAG]]
- [[Estudo - Agentic RAG no Second Brain]]
