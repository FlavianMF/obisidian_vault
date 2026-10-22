---
title: "How we built our multi-agent research system"
type: article
tags: [agentic-ai, multi-agent, evaluation, anthropic]
created: 2026-10-22
provenance: obsidian_vault
authors: Anthropic
year: 2025
source: https://www.anthropic.com/engineering/multi-agent-research-system
verified: 2026-10-22 via leitura da página com WebFetch (subagente de pesquisa)
confidence: low
seen_in: [obsidian_vault]
---

# How we built our multi-agent research system

Post · Anthropic · 2025 · <https://www.anthropic.com/engineering/multi-agent-research-system>

## 📝 Resumo

- Um lead Opus 4 com subagentes Sonnet 4 superou o Opus 4 sozinho em 90,2% no eval interno.
- O uso de tokens explica cerca de 80% da variância no BrowseComp. Agentes usam cerca de 4 vezes os tokens de um chat, e multiagente cerca de 15 vezes.
- Falhas vistas: subagentes demais para query simples, busca infinita por fonte inexistente, trabalho duplicado.
- Eval: comece com cerca de 20 queries reais, LLM judge com rubrica e humanos por cima. Julgue o estado final, não o caminho.

## Confiabilidade

Fonte primária, publicada em 13/06/2025. Já citada pela RFC-001 (E6).

## 🔗 Conexões

- [[Agentic RAG]]
- [[Estudo - Agentic RAG no Second Brain]]
