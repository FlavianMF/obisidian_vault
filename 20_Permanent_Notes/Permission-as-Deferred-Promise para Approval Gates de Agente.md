---
title: Permission-as-Deferred-Promise para Approval Gates de Agente
type: pattern
tags: [agentic-ai, permissions, approval-gate, async-architecture, tool-use]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

# Permission-as-Deferred-Promise para Approval Gates de Agente

Quando um agente LLM precisa de aprovação humana (ou de política) antes de
executar uma ação sensível (rodar shell, escrever arquivo, chamar tool
externa), **não bloquear o processo esperando input síncrono**. Em vez
disso: a tentativa de tool call cria uma promise/deferred pendente, publica
um evento anunciando o pedido, e a execução da tool fica suspensa até algo
externo resolver essa promise (`allow` / `deny` / `always`).

**Por que importa**: desacopla completamente o loop de execução do agente
do mecanismo de aprovação. A mesma tool call pode ser aprovada por um
humano numa UI interativa, por uma política programática (um hook que
decide em código), ou por um processo externo via chamada de API — sem
mudar nada no loop principal. O loop só sabe "esperar a promise resolver",
não "como" ela vai ser resolvida.

**Como fica concretamente** (caso observado em [[opencode]]):
- Regras declarativas resolvem pra `allow`/`ask`/`deny` por tool e por
  padrão glob de argumento (ex.: `git *` = allow, `rm *` = deny), com a
  última regra que casar vencendo.
- Se resolve pra `ask`, cria-se um `Deferred`, publica um evento
  `Asked`, e um endpoint de API (`POST .../permission/{id}/reply`)
  resolve a promise de fora.
- Um hook de plugin (`permission.ask`) pode interceptar *antes* mesmo de
  virar um pedido pendente — política totalmente programática, sem tocar
  UI nem endpoint.
- Regras `deny` explícitas nunca são bypassadas, nem por flags de
  auto-aprovação total (`--auto`, `--dangerously-skip-permissions`) — só
  ausência de regra + flag de bypass vira aprovação automática.

**Paralelo no protocolo MCP**: a primitiva `elicitation` (server pede,
usuário responde) e o design de `sampling` (server pede uma completion,
usuário controla se acontece e o que o server vê do resultado) seguem a
mesma lógica — pedir permissão como uma troca assíncrona explícita em vez
de assumir acesso implícito. Ver [[Model Context Protocol (MCP)]].

**Quando usar**: qualquer harness de agente que precise suportar tanto
aprovação interativa (humano na TUI/chat) quanto automação headless (CI,
batch) com a *mesma* lógica de decisão de permissão — sem duplicar o gate
pra cada modo.

## 🔗 Conexões
- [[opencode]]
- [[Model Context Protocol (MCP)]]
