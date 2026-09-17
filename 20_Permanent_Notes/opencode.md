---
title: opencode
type: concept
tags: [ai-agent, cli, harness, agent-architecture, tui, llm]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

# opencode

Agente de codificação open source (MIT) nativo de terminal —
[github.com/anomalyco/opencode](https://github.com/anomalyco/opencode),
docs em opencode.ai/docs. Monorepo TypeScript/Bun/Turborepo, backend em
**Effect-TS**, TUI em SolidJS+OpenTUI, persistência SQLite/Drizzle. Origem:
TermAI (Kujtim Hoxha, 2024) → rebrand OpenCode pelo time da SST (Dax Raad,
Adam Elmore) → org renomeada Anomaly em 2026 (fonte secundária, não
confirmada contra fonte primária).

Relevante como **estudo de caso de arquitetura de harness de agente**: é o
projeto open source mais maduro encontrado que separa explicitamente
cliente/servidor, expõe API HTTP+SSE completa, tem sistema de permissão
desacoplado do loop de execução, e plugins com hooks em todo o ciclo de
vida — direto aplicável ao design de tooling de agente próprio (ver
[[Model Context Protocol (MCP)]] pro protocolo que opencode consome como
client).

## Arquitetura em uma frase

Prompt do usuário → admitido numa inbox durável (event-sourced, "Session
V2") → loop externo (`prompt.ts`) chama um processor que consome um
**stream único de eventos do LLM por turno** (`llm.stream()`) → tool calls
emitidas pelo próprio modelo no meio do stream são executadas passando por
um gate de permissão assíncrono → resultado volta pro próximo chunk do
stream → repete até o modelo parar de pedir tool calls.

## Padrões extraídos (notas atômicas)

- [[Permission-as-Deferred-Promise para Approval Gates de Agente]]
- [[Transporte Plugável - Mesma API Client-Server In-Process ou HTTP Real]]
- [[Separar Protocol de Route em Abstração Multi-Provider de LLM]]

## Outras decisões de design notáveis

- **Multi-agente/subagentes** via tool `task`: sessão filha recebe
  permissões *derivadas e mais restritas* que a sessão pai (nega
  recursivamente `task` e `todowrite` por padrão) — evita fan-out
  descontrolado de subagentes sem precisar de lógica extra no loop
  principal, só herança de config.
- **Event-sourcing de sessão**: separa "admissão do prompt" (evento
  durável, queryable) de "execução do prompt" (side-effecting). Compaction
  automática troca só a *representação ativa* do modelo, preservando a
  transcrição completa — permite auditoria/replay sem re-executar contra o
  LLM.
- **Fail explicit**: combinação provider/rota não suportada falha com erro
  claro em vez de degradar silenciosamente — postura deliberada de
  confiabilidade sobre cobertura, relevante pra qualquer harness rodando
  sem supervisão humana constante (CI).

## Trap observado: namespace de API duplo sem depreciação sinalizada

O servidor expõe rotas REST legadas sem prefixo (`/session/...`) *e* um
namespace novo `/api/*` (`/api/session/...`) coexistindo, refletindo uma
migração V1→V2 em andamento sem aviso explícito de qual é o alvo
recomendado. Lição geral: ao integrar com uma API em migração, checar o
código-fonte/schema (não só a doc) pra confirmar qual geração é a
ativamente desenvolvida antes de construir dependência em cima dela.

## Pesquisa completa

Pesquisa detalhada (17 notas: stack, agent loop, client-server, providers,
tools, permissões, MCP, plugins, config, persistência, headless/SDK/API,
subagentes, auth, fontes) — [índice completo em 40_Projects/opencode](../40_Projects/opencode/00_indice.md).
Cópia espelhada também no projeto de origem `projetos_ita`, fora do vault:
`notes/research/opencode/00_indice.md`.

## Comparação com o outro harness estudado

[[claude-code]] resolve os mesmos problemas com um desenho bem diferente: em vez de API
HTTP + lista fixa de hooks, **toda chamada na API é ela própria um evento** numa cadeia de
cinco tiers de autoridade. Onde o opencode é mais forte: acesso externo de primeira classe
(REST+SSE+SDK+mDNS), abstração multi-provider explícita, e source legível sob MIT. Onde o
claude-code é mais forte: um modelo só para tudo, política organizacional inburlável por
assento, e testabilidade. Comparativo completo em
`40_Projects/claude_code/19_comparativo_opencode.md`.

## 🔗 Conexões
- [[Model Context Protocol (MCP)]]
- [[claude-code]]
- [[Permission-as-Deferred-Promise para Approval Gates de Agente]]
- [[Transporte Plugável - Mesma API Client-Server In-Process ou HTTP Real]]
- [[Separar Protocol de Route em Abstração Multi-Provider de LLM]]
- [Índice completo da pesquisa (40_Projects/opencode)](../40_Projects/opencode/00_indice.md)
