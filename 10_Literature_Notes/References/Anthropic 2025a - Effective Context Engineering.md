---
title: "Effective context engineering for AI agents"
type: article
tags: [agentic-ai, context-engineering, retrieval, anthropic, claude-code]
created: 2026-10-22
provenance: obsidian_vault
authors: Anthropic Engineering
year: 2025
source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
verified: 2026-10-22 via leitura da página com WebFetch (subagente de pesquisa)
confidence: low
seen_in: [obsidian_vault]
---

# Effective context engineering for AI agents

Post · Anthropic Engineering · 2025 · <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>

## 📝 Resumo

- Recuperação just-in-time: o agente guarda referências leves (paths, queries) e carrega o dado quando precisa.
- Divulgação progressiva: tamanho, nome e data do arquivo guiam o próximo passo.
- Híbrido no Claude Code: carrega o CLAUDE.md no início e usa glob e grep para o resto.
- Compactação, notas estruturadas (NOTES.md) e subagentes que devolvem resumos de 1 a 2 mil tokens.
- Trade-off: explorar em runtime é mais lento que usar dado pré-computado.

## Confiabilidade

Fonte primária, publicada em 29/09/2025. É a descrição mais próxima do que o second brain já faz com manifests.

## 🔗 Conexões

- [[Agentic RAG]]
- [[Estudo - Agentic RAG no Second Brain]]
