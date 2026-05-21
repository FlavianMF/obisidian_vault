---
title: Projeto hermes_validator
type: project
status: completed
tags: [project, agentic-ai, crewai, automation, education]
created: 2026-05-21
path: /home/flv/projetos_crewai/hermes_validator/workspace
---

# Projeto hermes_validator

Sistema de validação e avaliação técnica automatizada de entregas de alunos (IoT), utilizando agentes de IA e scripts de processamento em massa.

## 📌 Visão Geral
Este projeto utiliza a infraestrutura do [[hermes_docker]] para executar um pipeline de avaliação. Originalmente concebido com [[Multi-Agent Systems (MAS)]] via CrewAI, evoluiu para uma abordagem híbrida de alta performance.

## 🧠 Conceitos e Padrões Extraídos
- [[Orquestração Híbrida de Agentes]]: Uso de scripts para tarefas repetitivas e LLMs para análise qualitativa.
- [[Validação Acadêmica Automatizada]]: Aplicação de rubricas técnicas via código.
- [[Dashboard de Resultados Agênticos]]: Visualização consolidada de outputs de múltiplos agentes/processos.

## 🛠️ Componentes do Sistema
1. **iot_validator (CrewAI)**: Definição de agentes (Inspector, Specialist, Evaluator).
2. **resultado_validacao**: Scripts Python puros para processamento de 77+ alunos em alta velocidade (3 min).
3. **Plano de Validação**: Estratégia de substituição de CrewAI por scripts para ganho de 10x em performance.

## 📂 Arquivos Chave
- `iot_validator/AGENTS.md`: Referência de padrões modernos de CrewAI.
- `resultado_validacao/RELATORIO_FINAL.md`: Estatísticas de execução e comparação de performance.
- `resultado_validacao/FLUXOGRAMA.md`: Detalhamento do sistema híbrido (Auto + Manual).

## Links
- [[hermes_docker]] (Infraestrutura base)
- [[Agentic AI]] (Conceitos de autonomia)
- [[Engenharia de Sistemas]] (MOC)
