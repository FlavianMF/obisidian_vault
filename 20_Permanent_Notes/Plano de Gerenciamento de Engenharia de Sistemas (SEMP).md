---
title: Plano de Gerenciamento de Engenharia de Sistemas (SEMP)
type: concept
tags: [systems-engineering, management, nasa, incose, documentation, planning]
created: 2026-05-21
provenance: manual
---

# 📋 Systems Engineering Management Plan (SEMP)

O **SEMP** (Plano de Gerenciamento de Engenharia de Sistemas) é o documento mestre que detalha como o esforço técnico de um projeto será gerenciado. Ele serve como o "manual de operações" técnico para a equipe de engenharia.

## 🎯 Propósito
- Definir como os processos de SE serão aplicados.
- Estabelecer a organização técnica e responsabilidades.
- Integrar as disciplinas de especialidade (Segurança, Confiabilidade, HSI).
- Alinhar o esforço técnico com o Plano de Gerenciamento do Projeto (Project Plan).

## 🏛️ Estrutura Comparativa: NASA vs. INCOSE

### NASA (NPR 7123.1 / SP-2016-6105)
A estrutura da NASA é altamente prescritiva e focada nos **17 Processos Técnicos Comuns**.
1. **Objetivo e Escopo:** O que o documento cobre.
2. **Resumo Técnico:** Descrição do sistema e fronteiras do esforço.
3. **Integração do Esforço Técnico:** Organização, interfaces e especialidades.
4. **Implementação dos 17 Processos:** Detalhamento de como cada processo do [[NASA SE Engine]] será executado. Veja o [[Detalhamento dos Processos Técnicos no SEMP]].
5. **Inserção de Tecnologia:** Planos de maturidade (TRL).
6. **Matrizes de Conformidade:** Como o projeto atende aos requisitos da NPR.

### INCOSE / ISO 15288
Focado no framework internacional e em estágios do ciclo de vida.
1. **Resumo do Projeto Técnico:** Objetivos, premissas e restrições.
2. **Processo de SE:** Descrição dos processos (Técnicos, Gestão, Organizacionais).
3. **Modelo de Ciclo de Vida:** Escolha do modelo (Vee, Agile, Waterfall).
4. **Planejamento e Controle:** WBS Técnica, Marcos (Milestones) e Critérios de Entrada/Saída para revisões.
5. **Integração de Especialidades:** Foco nas "ilities" (Reliability, Availability, Maintainability).

## 🔄 O SEMP como Documento Vivo
O SEMP não é estático. Ele deve ser atualizado em cada **Key Decision Point (KDP)** ou revisão técnica importante (SRR, PDR, CDR) para refletir:
- Maturidade do design.
- Mudanças nos riscos técnicos.
- Tailoring (ajustes) dos processos conforme a complexidade do projeto.

## 🔗 Conexões
- [[Caso de Uso - SEMP Birthday Counter|Exemplo Prático: SEMP no Birthday Counter]]
- [[NASA SE Engine]]
- [[Ciclo de Vida de Engenharia de Sistemas]]
- [[Análise de Trade-off (Trade Study)]]
- [[Engenharia de Sistemas (MOC)]]

---
*Referência: NASA SE Handbook (App J) e INCOSE SE Handbook.*
