---
title: "Model Context Protocol — Specification (2025-11-25)"
type: article
tags: [mcp, llm, protocol, spec]
created: 2026-08-14
provenance: capella_mcp
authors: Model Context Protocol (Linux Foundation / modelcontextprotocol org)
year: 2025
citekey: MCP2025
---

# Model Context Protocol — Specification (2025-11-25)

## 📝 Resumo
- Especificação normativa do protocolo MCP, versão `2025-11-25`. Define
  formato de mensagens (JSON-RPC 2.0), ciclo de vida da conexão
  (initialize/operation/shutdown), primitivas (resources, tools, prompts do
  lado servidor; sampling, roots, elicitation do lado cliente) e princípios
  de segurança/consentimento do usuário.

## 💡 Principais Insights
- Três papéis: **Host** (app que inicia a conexão) → **Client** (conector
  dentro do host) → **Server** (expõe contexto/capacidades). Inspirado no
  Language Server Protocol.
- `tools` são **model-controlled** (o modelo decide chamar); `prompts` são
  **user-controlled** (usuário aciona explicitamente, ex. slash command);
  `resources` ficam sob controle da aplicação.
- Handshake (`initialize`) negocia capabilities e devolve um campo
  `instructions` (texto livre do server pro client) — mecanismo mais
  próximo de um "system prompt" embutido no protocolo.
- Tool `description`/`annotations` funcionam como prompt engineering
  implícito, mas devem ser tratadas como *untrusted* a menos que venham de
  server confiável (risco de tool description injection).
- Convenção `isError: true` no resultado de uma tool call dá feedback
  acionável pro modelo se autocorrigir, distinto de erro de protocolo
  JSON-RPC.
- Segurança: consentimento explícito do usuário obrigatório pra exposição
  de dados, invocação de tool e qualquer `sampling` request; protocolo
  limita de propósito a visibilidade do server sobre o prompt exato
  enviado numa `sampling` request.

## 🔗 Conexões (Zettelkasten)
- [[Model Context Protocol (MCP)]]
- [[Soria Parra & Spahr-Summers 2024]]

---
## 📑 Citação Completa
> MODEL CONTEXT PROTOCOL. Specification (2025-11-25). Linux Foundation / modelcontextprotocol org, 2025.

**Acesso**: [modelcontextprotocol.io/specification/2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) — Acesso em: 14 ago. 2026.
