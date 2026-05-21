---
title: Engenharia de Sistemas Agêntica (Agentic Systems Engineering)
type: pattern
project: birthday_counter
tags: [agentic-ai, systems-engineering, automation, architecture]
created: 2026-05-21
provenance: 1.0
---

# Engenharia de Sistemas Agêntica (Agentic Systems Engineering)

Padrão de desenvolvimento onde um [[Agentic AI|Agente de IA]] (como o [[hermes_docker|Hermes]]) utiliza princípios formais de [[MBSE|Engenharia de Sistemas (SE)]] para autogovernar o [[Ciclo de Vida de Engenharia de Sistemas|Ciclo de Vida]] de um software, desde a concepção até a implementação.

## Características do Padrão
1. **Autoconstrição via "Hardened Guidelines"**: O agente define diretrizes técnicas imutáveis (ex: `systems_engineering_foundation.md`) antes de escrever código. Isso evita o "drift" arquitetural em sessões longas.
2. **Modelagem de Estados (FSM)**: Definição formal de estados do sistema (ex: `PRE_EVENT`, `CLIMAX`, `POST_EVENT`) para garantir comportamento previsível.
3. **Mapeamento de Stakeholders**: Identificação de atores humanos e sistêmicos (AI Engine) para derivar requisitos funcionais e de interface.
4. **Alinhamento com Fases SE (NASA/INCOSE)**:
    - **[[Pré-Fase A - Análise de Conceito|Pré-Fase A]]/[[Fase A - Desenvolvimento de Conceito|Fase A]]**: Criação de [[PRD]], [[stakeholders|Stakeholder Matrix]] e [[user_journeys|User Journeys]].
    - **[[Fase B - Definição Preliminar|Fase B]]**: Definição da Stack, Esquema de Banco de Dados e Contratos de API.

## Vantagens
- **Integridade Técnica**: O código gerado é aderente a uma arquitetura pré-definida, não apenas funcional.
- **Traceability**: Requisitos no [[PRD]] são diretamente mapeados para componentes no código.
- **Escalabilidade**: Facilita a entrada de novos agentes (ou humanos) no projeto através de uma base de conhecimento robusta.

## Links
- [[Ciclo de Vida de Engenharia de Sistemas]]
- [[Agentic AI]]
- [[birthday_counter]]

## Fontes
- Projeto: `birthday_counter`
- Documentação: `systems_engineering_foundation.md`, `PRD.md`, `stakeholders.md`
