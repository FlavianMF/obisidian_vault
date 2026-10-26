---
title: Traycer - Workspace de Agentes em Worktrees Paralelas
type: concept
tags: [agentic-ai, orchestration, traycer, tooling, worktree]
created: 2026-10-26
provenance: obsidian_vault
seen_in: [obsidian_vault]
verified: 2026-10-26 via traycer.ai (home) e buscas web
confidence: low
---

# Traycer - Workspace de Agentes em Worktrees Paralelas

Camada de **orquestração do trabalho** dos agentes (plano, execução, revisão). Não roteia modelos: isso é papel do roteador, ver [[CCR - Gateway Local de Modelos para Agentes de Código]].

## O que é
- App desktop gratuito e open source (Mac, Windows, Linux) em https://traycer.ai/.
- Cada agente roda em seu próprio worktree. Specs, tickets e artefatos são compartilhados por Task.
- Agentes trocam mensagens: perguntam, pedem revisão e passam trabalho adiante.
- Skills embutidas: `/plan`, `/execute`, `/review`, `/debate`, e quebra em tickets. "Epic Mode" cobre trabalho grande.
- O plano pode ser corrigido antes de qualquer código. Troca de modelo no meio do chat sem perder o fio.
- Traz a assinatura própria (Claude Code, Codex, Cursor, OpenCode). Plano Free sem medição de tokens.
- Plano Sync: US$16 por usuário ao mês (anual) ou US$20 (mensal), para colaboração em equipe. Créditos Traycer e sandboxes na nuvem são pagos à parte.

## Ressalvas
- A home diz 22 agentes suportados, mas o FAQ lista só 4. A página não reconcilia.
- Resenhas antigas o descrevem como camada de plano e verificação em VS Code e forks. O produto atual é app standalone.
- Fontes independentes são poucas e parte vem do lançamento. Sem benchmark comparativo.
- A página não detalha fases nem verificação além de `/review`.

## Alternativas citadas em comparativos (2026)
- Claude Squad: TUI em Go, AGPL-3.0, tmux + worktree por agente.
- Conductor: app macOS para sessões paralelas de Claude Code e Codex. Fontes divergem no preço.
- Vibe Kanban: quadro kanban. Uma fonte diz que a empresa encerrou em 2026-04-10. Código segue Apache-2.0, manutenção incerta.
- Agent Teams: orquestração nativa do Claude Code (`/team`). Pode bastar para paralelismo simples.
- Superset, Agent-Manager, Pane, Golutra: só vistos em comparativos, não verificados. ccswarm: sem resultado.

Contexto de uso: [[Orquestração Híbrida de Agentes]] e a RFC-002 do projeto second_brain_memory.

## O que NÃO funcionou
Nada foi testado. É leitura de fontes públicas, nenhuma ferramenta foi instalada ou rodada. Por isso `confidence: low`.
