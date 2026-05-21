---
title: Processo de Definição Pré-Desenvolvimento (Elite SE Workflow)
type: pattern
tags: [systems-engineering, mbse, sysml-v2, agentic-ai, workflow]
created: 2026-05-21
provenance: Academic Research 2024-2025 + 3 Pilares Framework
---

# 🚀 Processo de Definição Pré-Desenvolvimento

Este guia estabelece o fluxo rigoroso de **Engenharia de Sistemas Agêntica** que deve preceder qualquer linha de código ou prototipagem física. O objetivo é garantir que a solução seja tecnicamente íntegra, rastreável e validada contra as dores reais dos stakeholders.

---

## 🏗️ Fase 0: O Alinhamento do "Problema de Elite" (Pilar 1)
*Baseado em Análise Operacional e Contexto de Missão.*

1.  **Mapeamento de Atores e Ecossistema**:
    - Não liste apenas usuários; identifique sistemas legados, APIs externas, restrições regulatórias e o ambiente físico.
    - **Artefato**: SysML Use Case Diagram (v2 Textual).
2.  **Narrativa de ConOps (Concept of Operations)**:
    - Descreva o "Cenário de Sucesso". Como a vida do ator muda com a solução?
    - **Ação**: Utilize LLMs para gerar 3 cenários extremos (Sucesso Total, Falha de Infraestrutura, Uso por Leigo).
3.  **Análise de Fluxo "As-Is" vs "To-Be"**:
    - Identifique exatamente onde o valor é gerado.
    - **Artefato**: Activity Diagram focado em **Troca de Valor** e **Pontos de Dor**.

## ⚙️ Fase 1: Especificação da "Black Box" (Pilar 2)
*Definindo O QUE o sistema faz sem se comprometer com a tecnologia.*

1.  **Derivação de Requisitos de Missão (L1)**:
    - Cada requisito deve ter uma tag `:refines` apontando para uma dor do Pilar 1.
    - **Padrão**: Requisito = [Ator/Sistema] + [Verbo de Ação] + [Objeto] + [Restrição].
2.  **Definição de Estados e Modos (FSM)**:
    - Antes de codar, defina como o sistema se comporta em: *Boot, Standby, Operational, Maintenance, Failsafe*.
    - **Artefato**: SysML State Machine Diagram.
3.  **Fronteira Formal (System Boundary)**:
    - Defina exatamente o que entra (Input) e o que sai (Output) de dados e energia.
    - **Artefato**: Block Definition Diagram (BDD) de Contexto.

## 📐 Fase 2: Arquitetura Lógica e Tradução (Pilar 3 - Parte A)
*A ponte entre a ideia e a implementação.*

1.  **Decomposição Funcional (Arquitetura Lógica)**:
    - Agrupe funções em blocos conceituais (ex: "Módulo de Percepção", "Orquestrador de Decisão").
    - **Vantagem**: Permite trocar o hardware no futuro sem redesenhar a lógica.
2.  **Definição de Interfaces (ICD - Interface Control Document)**:
    - Especifique protocolos (MQTT, gRPC, I2C) e o schema dos dados antes de criar as classes.
    - **Artefato**: Internal Block Diagram (IBD) detalhando os **Item Flows**.
3.  **Análise Paramétrica (Budgeting)**:
    - Defina os limites: Latência máxima, consumo de RAM, autonomia de bateria.
    - **Artefato**: Parametric Diagram (Validação Matemática Preliminar).

## 🤖 Fase 3: Validação Acadêmica e Agêntica (Check-Gate)
*O uso de IA para garantir que nada foi esquecido.*

1.  **Audit de Rastreabilidade**:
    - Um agente de IA deve verificar: "Existe algum bloco na arquitetura que não satisfaz um requisito?" ou "Existe algum requisito sem conexão com uma dor do Pilar 1?".
2.  **Simulação MiL (Model-in-the-Loop)**:
    - Utilize o modelo SysML v2 para simular o comportamento lógico antes da implementação.
3.  **Geração do Digital Product Passport (DPP)**:
    - Inicie o tracking de materiais e dependências para sustentabilidade e ciclo de vida longo.

---

## 📝 Como Aplicar Hoje
Para cada nova solução, crie um arquivo `DEFINITIONS.md` no folder do projeto seguindo esta estrutura:
1. **Stakeholder Matrix** (Quem se importa?)
2. **Requirement Tree** (Por que estamos fazendo isso?)
3. **Logic Blocks** (Como as peças se encaixam?)
4. **Interface Schemas** (Como as peças conversam?)

---
## 🔗 Conexões
- [[Engenharia de Sistemas Agêntica]]
- [[Aplicação do SysML nos 3 Pilares]]
- [[Framework 3 Pilares SE]]
- [[MBSE com Agentic AI]]
