---
title: Visão geral e história
type: project
tags: [opencode, ai-agent, history, oss]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

> Ver [[opencode]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Visão geral e história

[← Índice](00_indice.md)

## O que é

**opencode** — tagline oficial (GitHub): *"The open source coding agent."* Docs: *"AI coding agent built for the terminal."*

Agente de codificação autônomo e nativo de terminal: aponta para um projeto, descreve o que quer em linguagem natural, e o agente lê arquivos, edita código, roda comandos de shell e pede permissão ao longo do processo (via [opencode.ai/docs](https://opencode.ai/docs/)).

Público-alvo: desenvolvedores que vivem no fluxo terminal/neovim/tmux, e times que querem uma alternativa multi-provider a ferramentas fechadas e single-vendor. Terceiros descrevem o projeto como "feito por usuários de neovim e pelos criadores da terminal.shop".

## Proposta de valor vs. alternativas (Claude Code, Aider, Cursor CLI)

- **Provider-agnostic**: Anthropic, OpenAI, Google, Amazon Bedrock, Azure, DeepSeek, Groq, Together AI, Fireworks, xAI, OpenRouter, modelos locais (Ollama, LM Studio, llama.cpp), credenciais GitHub Copilot/GitLab Duo, e qualquer endpoint OpenAI-compatible — 75+ providers via AI SDK + integração com Models.dev (ver [05_providers_llm.md](05_providers_llm.md)).
- **Arquitetura client/server explícita** (diferente da maioria dos agentes CLI single-process): `opencode` sobe TUI + servidor HTTP; a TUI é só um cliente entre vários possíveis (plugins de IDE, web UI, SDK clientes customizados podem falar com o mesmo servidor) — ver [04_client_server.md](04_client_server.md).
- **Múltiplos front-ends**: TUI, servidor headless (`opencode serve`), web UI (`opencode web`), app desktop (beta, macOS/Windows/Linux), integrações de IDE/editor, suporte a Agent Client Protocol (ACP).
- **Open source / self-hostable**, MIT, vs. Claude Code (closed source, single-vendor) — comparável em espírito ao Aider (open, multi-provider), mas com arquitetura client/server/plugin/SDK mais completa e TUI nativa em vez de um REPL simples.

Comparação independente encontrada: "Pi vs OpenCode: After 100 Hours" ([composio.dev/content/pi-vs-opencode](https://composio.dev/content/pi-vs-opencode)).

## História, mantenedores, licença

**Aviso de confiabilidade da fonte:** os detalhes de rebranding/organização abaixo vieram de blogs/wikis de terceiros (Medium, DEV.to, TechFundingNews, DataCamp, aiwiki.ai, Grokipedia, developersdigest.tech), não de uma fonte primária da Anomaly/SST verificada diretamente nesta pesquisa. O formato geral da história (disputa OpenCode/Charm/Crush) é consistente com contexto público já conhecido sobre esse espaço, mas datas/números exatos merecem checagem antes de citar como fato definitivo.

- Origem: agente anterior chamado **"TermAI"**, criado por Kujtim Hoxha (2024).
- **Dax Raad** e **Adam Elmore** (time por trás da **SST**, framework de infraestrutura serverless) fizeram o rebrand para OpenCode.
- SST rebrandeou a empresa/org como **"Anomaly"** em 2026; o repositório hoje vive em `github.com/anomalyco/opencode` (org GitHub `anomalyco`, ID 66570915).
- Disputa relatada: **Charm** (criadores de Bubbletea/Lipgloss) teria tentado trazer o projeto para sua org e contratado Hoxha; Raad/Doty (donos do domínio opencode.ai) mantiveram o nome OpenCode, e a versão da Charm foi renomeada para **"Crush"**.
- Curiosidade que corrobora a linhagem SST: o repositório ainda contém `sst.config.ts`/`sst-env.d.ts` na raiz e em praticamente todo package — indica que SST continua sendo usado para o deploy da infraestrutura do próprio projeto, mesmo após o rebrand da org.

**Licença:** MIT (confirmado via GitHub API, `license.spdx_id: "MIT"`).

**Estatísticas do repositório** (via `api.github.com/repos/anomalyco/opencode`, snapshot da pesquisa): 205.857 stars, 26.871 forks, 5.714 issues abertas, criado em 2025-04-30, com push recente no dia da pesquisa. Homepage: `https://opencode.ai`.
*Obs.: números de stars variaram entre fetches (205,9k vs. ~160k) — provavelmente cache/snapshot diferente do WebFetch; não tratar como precisos, só como ordem de grandeza ("centenas de milhares de stars, projeto muito ativo").*

**Sinal de comunidade internacional:** o repositório tem 22 READMEs traduzidos (ar, bn, br, bs, da, de, es, fr, gr, it, ja, ko, no, pl, ru, th, tr, uk, vi, zh, zht).

## Governança

`CONTRIBUTING.md`: contribuições de produto/UI exigem revisão de design com o time principal antes; correções de bug/providers/LSP são aceitas mais livremente. O documento desencoraja explicitamente "descrições de PR longas e geradas por IA" — uma declaração pequena mas reveladora sobre como os mantenedores querem que o código evolua.
