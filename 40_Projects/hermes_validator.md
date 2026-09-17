---
title: Projeto hermes_validator
type: project
tags: [project, agentic-ai, crewai, automation, education]
created: 2026-05-21
provenance: manual
status: archived
path: (removido do disco)
verified: 2026-09-17 via ls do sistema de arquivos
successor: /home/flv/projetos_pnaat/validacoes_iot
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

## ⚠️ Estado (verificado em 2026-09-17)
O caminho original `/home/flv/projetos_crewai/hermes_validator/workspace` **não existe mais no
disco**. O pipeline vivo que sucede este projeto é `/home/flv/projetos_pnaat/validacoes_iot`
(mesma arquitetura: `00_run_all.py`, `scripts/`, `data/`, `reports/`, rubrica em
`docs/rubrica_iot.md` com correção manual em estrelas 0-3). A correção conversacional de um repo
por vez, derivada daqui, vive em `/home/flv/projetos_pnaat/correcoes_docs_tcc` — ver
[[correcoes_docs_tcc]] e [[Rubrica em Prosa Vira Gabarito de Evidência]].

## Links
- [[correcoes_docs_tcc]] (o sucessor conversacional, com primeiro lote concluído)
- [[hermes_docker]] (Infraestrutura base)
- [[Agentic AI]] (Conceitos de autonomia)
- [[Engenharia de Sistemas]] (MOC)
