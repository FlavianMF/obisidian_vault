---
title: "Introducing the Model Context Protocol"
type: article
tags: [mcp, llm, protocol]
created: 2026-08-14
provenance: capella_mcp
authors: Soria Parra, David; Spahr-Summers, Justin
year: 2024
citekey: SoriaParra2024
---

# Introducing the Model Context Protocol

## 📝 Resumo
- Anúncio oficial da Anthropic (25/11/2024) do MCP: protocolo aberto,
  baseado em JSON-RPC 2.0, pra conectar aplicações LLM (hosts) a fontes de
  contexto e ferramentas externas via um client/server padronizado.

## 💡 Principais Insights
- Problema que motivou: cada integração LLM↔ferramenta era construída ad
  hoc; MCP propõe um protocolo único em vez de N integrações customizadas.
- Modelo cliente-servidor de duas vias: servers expõem dados/tools, clients
  (embutidos em apps como Claude Desktop) se conectam a eles.
- Lançado junto com SDKs e um repositório de servers pré-construídos
  (Google Drive, Slack, GitHub, Git, Postgres, Puppeteer).

## 🔗 Conexões (Zettelkasten)
- [[Model Context Protocol (MCP)]]
- [[Model Context Protocol 2025]]

---
## 📑 Citação Completa
> SORIA PARRA, David; SPAHR-SUMMERS, Justin. Introducing the Model Context Protocol. Anthropic, 25 nov. 2024.

**Acesso**: [Anthropic News](https://www.anthropic.com/news/model-context-protocol) — Acesso em: 14 ago. 2026.
