---
title: CCR - Gateway Local de Modelos para Agentes de Código
type: concept
tags: [agentic-ai, routing, ccr, claude-code-router, tooling, tokens]
created: 2026-10-26
provenance: obsidian_vault
seen_in: [obsidian_vault]
verified: 2026-10-26 via README em github.com/musistudio/claude-code-router
confidence: low
---

# CCR - Gateway Local de Modelos para Agentes de Código

CCR (claude-code-router) é um **roteador de chamadas de modelo**, não um orquestrador de tarefas. Para a camada de trabalho, ver [[Traycer - Workspace de Agentes em Worktrees Paralelas]]. Para custo por camada, ver [[Router de Tokens em 3 Camadas - Carga, Contexto e Modelo]].

## O que é
- Gateway local (padrão `127.0.0.1:3456`). Recebe chamadas de Claude Code, Codex, OpenCode e outros. Encaminha ao provedor configurado.
- Roteamento por header ou corpo, prefixos, reescrita de request, retry e fallback ordenado de modelos.
- Protocolos: OpenAI Chat/Responses, Anthropic Messages, Gemini. Provedores: OpenRouter, DeepSeek, Moonshot, Mistral, Z.AI e compatíveis custom.
- Rotação de chaves, chaves de cliente com expiração e limites, logs de provedor, latência, tokens e custo estimado.
- Extras: fusion models (visão ou busca web sobre modelo existente), ToolHub, MCP, plugins, relay por Slack/Discord/Telegram.
- MIT, cerca de 38k estrelas. Instalação: `npm install -g @musistudio/claude-code-router` (Node 22+). UI: `ccr ui`. Também há app desktop e Docker.
- Docs completas em ccrdesk.top.

## Ressalvas
- O README não documenta o formato do config nem transformers. Consultar ccrdesk.top antes de depender disso.
- Antes de expor via Docker, ler o guia de deploy: o gateway guarda chaves de provedor.

## O que NÃO funcionou
Nada foi testado. É leitura do README, nenhuma instalação ou execução. Por isso `confidence: low`.
