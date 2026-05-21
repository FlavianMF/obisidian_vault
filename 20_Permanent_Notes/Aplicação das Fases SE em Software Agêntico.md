---
title: Aplicação das Fases SE em Software Agêntico
type: concept
project: birthday_counter
tags: [systems-engineering, lifecycle, nasa-se, agents]
created: 2026-05-21
provenance: 1.0
---

# Aplicação das Fases SE em Software Agêntico

Mapeamento de como os agentes de IA podem executar as fases do Ciclo de Vida de Engenharia de Sistemas (NASA/INCOSE) no contexto de desenvolvimento de software.

## Mapeamento de Fases
### 1. Pré-Fase A (Análise de Conceito)
- **Ação do Agente**: Identificação de Stakeholders e criação da Matriz de Interação.
- **Output**: [[stakeholders.md]].

### 2. Fase A (Desenvolvimento de Conceito)
- **Ação do Agente**: Definição de User Journeys e Product Requirements Document (PRD).
- **Output**: [[PRD.md]], [[user_journeys.md]].

### 3. Fase B (Definição Preliminar)
- **Ação do Agente**: Estabelecimento da fundação técnica, stack, arquitetura de dados e máquina de estados.
- **Output**: [[systems_engineering_foundation.md]], [[db_schema.md]], [[api_design.md]].

## Por que usar SE em Projetos Agênticos?
Agentes tendem a ser míopes (turn-by-turn). O rigor das fases SE força o agente a estabelecer um contexto global e restrições técnicas que servem como "âncora" para a geração de código subsequente, garantindo que o sistema final atenda aos objetivos dos stakeholders originais.

## Links
- [[Pré-Fase A - Análise de Conceito]]
- [[Fase A - Desenvolvimento de Conceito]]
- [[Fase B - Definição Preliminar]]
- [[Engenharia de Sistemas Agêntica]]

## Fontes
- Projeto: `birthday_counter`
- Documentação: `docs/index.md`
