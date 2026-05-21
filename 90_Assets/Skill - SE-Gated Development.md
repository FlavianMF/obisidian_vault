---
title: Skill: SE-Gated Development
type: pattern
tags: [agentic-ai, systems-engineering, quality-gate]
created: 2026-05-21
---

# Skill: SE-Gated Development

## Comportamento
O agente **recusa-se a escrever código** sem verificar requisitos prévios.

## Regras
1. **Verificação de Fase**: Antes de iniciar, o agente deve checar se a fase atual do projeto (PRD, Arquitetura) está documentada em `docs/`.
2. **Hardened Guidelines**: Se for uma tarefa de implementação, o agente deve validar se a decisão atende às diretrizes definidas em [[Engenharia de Sistemas Agêntica]].
3. **Pausa para Aprovação**: Em decisões de arquitetura não triviais, o agente deve apresentar a solução proposta e aguardar confirmação antes de alterar código fonte.
