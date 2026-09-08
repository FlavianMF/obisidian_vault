---
title: Pesquisa: opencode (anomalyco/opencode) — Arquitetura para Harness
type: moc
tags: [moc, opencode, ai-agent, harness, agent-architecture]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

# Pesquisa: opencode (anomalyco/opencode) — Arquitetura para Harness

> Repositório: [github.com/anomalyco/opencode](https://github.com/anomalyco/opencode) · Docs: [opencode.ai/docs](https://opencode.ai/docs/) · Licença: MIT
> Pesquisa realizada em 2026-09-08 via WebFetch/WebSearch/GitHub API. **Branch default do repositório é `dev`, não `main`** — qualquer link `raw.githubusercontent.com` ou clone deve usar `dev`.

## Por que essa pesquisa

opencode é a referência mais próxima e mais madura de "agente de codificação com arquitetura própria de harness" disponível como open source hoje: separa cliente/servidor, expõe API HTTP+SSE completa, tem sistema de permissões desacoplado do loop de execução, plugins com hooks em todo o ciclo de vida, e um design explícito de multi-provider LLM. Serve como estudo de caso direto para o desenvolvimento de um harness próprio de orquestração de agentes (MCP/LLM tooling em torno do Capella — ver `notes/arquitetura_hibrida_mcp_capella.md` e `notes/metodologia_dev_mcp.md`).

## Nota de segurança (transparência sobre a pesquisa)

Um dos agentes de pesquisa (WebFetch em `opencode.ai/docs/cli`) sinalizou automaticamente que o texto capturado continha o padrão `--dangerously-skip-permissions`. Isso é uma **flag real e documentada do próprio opencode** (bypassa o sistema de permissões, usada para automação/CI) — não é injeção de prompt, apenas um heurístico de segurança do harness de pesquisa reagindo ao nome da flag. Documentado com destaque em [07_permissoes_seguranca.md](07_permissoes_seguranca.md) porque é justamente o tipo de flag que um harness precisa tratar com cuidado (ver `experimental.policies` como camada complementar de hard-block).

## Índice dos arquivos

| # | Arquivo | Conteúdo |
|---|---|---|
| 01 | [Visão geral e história](01_visao_geral_historia.md) | O que é opencode, proposta de valor, comparação com Claude Code/Aider, origem do projeto (TermAI → SST → Anomaly), disputa Charm/Crush |
| 02 | [Stack e monorepo](02_stack_monorepo.md) | TypeScript/Bun/Turborepo/Effect-TS/SolidJS, tabela completa de packages |
| 03 | [Agent loop](03_agent_loop.md) | Modelo de execução prompt → stream LLM → tool calls → permission check; Session V2 event-sourced |
| 04 | [Client/server](04_client_server.md) | HTTP REST + SSE + WebSocket, RPC in-process vs HTTP real, mDNS |
| 05 | [Providers LLM](05_providers_llm.md) | Abstração multi-provider própria + Vercel AI SDK, ordem de resolução de config |
| 06 | [Sistema de tools](06_sistema_tools.md) | Tools built-in, dois esquemas de schema (Effect Schema vs Zod), custom tools |
| 07 | [Permissões e segurança](07_permissoes_seguranca.md) | Modelo allow/ask/deny, fluxo request/deferred, flags de bypass, policies |
| 08 | [MCP](08_mcp.md) | Cliente MCP oficial, config local/remoto, OAuth/DCR |
| 09 | [Plugins](09_plugins.md) | Hooks completos do ciclo de vida — principal ponto de automação via código |
| 10 | [Configuração](10_configuracao.md) | `opencode.json`, ordem de merge, XDG dirs, schemas publicados |
| 11 | [Persistência de sessão](11_persistencia_sessao.md) | SQLite/Drizzle, resume/fork/continue, export/import/share |
| 12 | [Headless, SDK e API (foco harness)](12_headless_sdk_api.md) | `opencode run`/`serve`, SDK TypeScript, rotas REST, ACP |
| 13 | [Multi-agente e subagentes](13_multiagente_subagentes.md) | Tool `task`, agentes built-in e customizados, permissões derivadas |
| 14 | [Autenticação](14_autenticacao.md) | `auth.json`, tipos de credencial, providers locais |
| 15 | [Implicações de design para harness próprio](15_implicacoes_harness.md) | Síntese: o que copiar, riscos observados |
| 16 | [Fontes](16_fontes.md) | Lista consolidada de URLs |

## Leitura recomendada por objetivo

- **Quer só entender o que é o projeto:** 01 → 02
- **Quer entender como o agente decide o que fazer:** 03 → 06 → 07
- **Quer construir automação/CI em cima do opencode:** 12 → 09 → 07 → 04
- **Quer decidir arquitetura do harness próprio (não usar opencode diretamente):** 15 (lê as outras por referência conforme citado)

## 🔗 Relacionado
- [[opencode]] — nota-conceito, âncora e síntese
- [[Permission-as-Deferred-Promise para Approval Gates de Agente]]
- [[Transporte Plugável - Mesma API Client-Server In-Process ou HTTP Real]]
- [[Separar Protocol de Route em Abstração Multi-Provider de LLM]]
- [[Model Context Protocol (MCP)]]
