---
title: Orquestração Híbrida de Agentes
type: pattern
project: hermes_validator
tags: [agentic-ai, architecture, performance, optimization]
created: 2026-05-21
provenance: 1.0
---

# Orquestração Híbrida de Agentes

Padrão arquitetural que combina scripts determinísticos (Python/Bash) para processamento pesado com agentes de IA (LLMs) para tarefas de alto nível e discernimento qualitativo.

## Descrição
Em sistemas de larga escala (ex: avaliar 100+ repositórios), o uso de agentes para todas as etapas (clone, listagem de arquivos, extração de texto) gera overhead de tokens, tempo e custo. O padrão híbrido delega a "força bruta" a scripts e a "inteligência" aos agentes.

## Aplicação no hermes_validator
- **Scripts (Python)**: Clone de 77 repositórios, extração de links via Regex, geração de relatórios Markdown e consolidação CSV.
- **Agentes (LLM)**: Análise da lógica do firmware, feedback qualitativo personalizado e revisão de documentação.

## Vantagens
- **Velocidade**: Ganho de até 10x comparado a frameworks de agentes puros (ex: CrewAI).
- **Custo**: Redução drástica no consumo de tokens.
- **Confiabilidade**: Scripts determinísticos não sofrem de alucinações em tarefas de IO.

## Links
- [[hermes_validator]]
- [[Agentic AI]]

## Fontes
- Projeto: `hermes_validator`
- Documentação: `RELATORIO_FINAL.md`, `plano_validacao_iot.md`
