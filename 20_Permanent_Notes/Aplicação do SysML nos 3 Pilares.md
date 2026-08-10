---
title: Aplicação do SysML nos 3 Pilares da SE
type: concept
tags: []
created: 2026-05-21
provenance: manual
---

# Aplicação do SysML nos 3 Pilares da SE

Este documento descreve como utilizar os diagramas SysML para modelar cada fase do framework de [[Framework 3 Pilares SE]], facilitando a transição entre a definição do problema e a implementação da solução.

---

## 🟦 Pilar 1: O Problema (Análise Operacional)
**Foco**: Entender o contexto e as dores dos stakeholders.

- **Use Case Diagram**: Mapeia os Atores (humanos/sistemas) e suas intenções.
- **Activity Diagram (Operacional)**: Modela o fluxo de trabalho atual ("As-Is") para identificar falhas e desperdícios.
- **Sequence Diagram (Cenários)**: Narra a interação entre o mundo externo e a "ideia" do sistema através de cenários de uso (ConOps).

## 🟩 Pilar 2: O Sistema (Análise de Requisitos)
**Foco**: Definir "O QUE" o sistema deve fazer (Black Box).

- **Requirement Diagram**: Documenta requisitos textuais e estabelece relações de hierarquia e derivação.
- **Block Definition Diagram (bdd - Contexto)**: Define formalmente a fronteira do sistema (System Boundary).
- **State Machine Diagram**: Define os modos (ex: Standby, Ativo, Erro) e estados de operação.
- **Functional Activity Diagram**: Transforma atividades operacionais em funções técnicas do sistema.

## 🟨 Pilar 3: A Solução (Arquitetura e Implementação)
**Foco**: Definir "COMO" construir (White Box).

- **Block Definition Diagram (bdd - Estrutura)**: Decomposição física em subsistemas, módulos e componentes (ex: Sensores, MCU, Cloud).
- **Internal Block Diagram (ibd)**: Modela as **Interfaces (ICDs)**. Define os fluxos (Item Flows) de dados, energia e sinal entre componentes.
- **Parametric Diagram**: Modela restrições matemáticas (ex: link budget, consumo de energia, latência) para validar a performance da solução.
- **Sequence Diagram (Design)**: Detalha a troca de mensagens entre componentes internos para realizar uma função específica.

---

## 🔄 Rastreabilidade no Ciclo de Vida
A grande vantagem do SysML neste framework é a **Rastreabilidade**:
1. Um **Bloco** (Pilar 3) `satisfies` um **Requisito** (Pilar 2).
2. Um **Requisito** (Pilar 2) `refines` um **Caso de Uso** ou **Atividade** (Pilar 1).

Essa estrutura é a base para o [[MBSE com Agentic AI]], onde agentes podem verificar automaticamente se a solução (Pilar 3) atende à dor original (Pilar 1).

---
## 🔗 Conexões
- [[SysML]]
- [[Framework 3 Pilares SE]]
- [[MBSE]]
- [[Engenharia de Sistemas Agêntica]]