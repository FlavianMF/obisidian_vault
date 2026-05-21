---
title: Caso de Uso - SEMP aplicado ao Birthday Counter
type: pattern
tags: [systems-engineering, semp, use-case, web-development, nasa-standard]
created: 2026-05-21
---

# 🚀 Caso de Uso: SEMP aplicado ao Birthday Counter

Este documento apresenta a aplicação hipotética do **Plano de Gerenciamento de Engenharia de Sistemas (SEMP)** ao projeto **Birthday Counter**, utilizando o padrão NASA (17 Processos Técnicos) adaptado para o contexto de desenvolvimento web moderno.

## 📌 Contexto do Projeto
O *Birthday Counter* é um sistema de celebração gamificada que utiliza IA, geolocalização e eventos em tempo real para criar "Cápsulas do Tempo" digitais.

---

## 🏗️ 1. Processos de Design do Sistema (5.1 - 5.4)

### 5.1 Stakeholder Expectations (Definição de Expectativas)
- **Método**: Entrevistas com "Sponsors" (organizadores) e "Hosts" (aniversariantes).
- **Ferramenta**: `docs/stakeholders.md` e Matriz de Interação.
- **Métrica**: Cobertura de personas (Admin, Host, Guest, Sponsor).

### 5.2 Technical Requirements (Requisitos Técnicos)
- **Método**: Tradução do PRD em requisitos "Shall" (devem).
- **Exemplo**: "O sistema *deve* emitir um evento WebSocket `CELEBRATION_TRIGGER` em menos de 100ms após o trigger do cron."
- **Ferramenta**: [[docs/PRD.md]] e Git Issues.

### 5.3 Logical Decomposition (Decomposição Lógica)
- **Método**: Modelagem Funcional via Diagramas de Atividade para o motor de gamificação.
- **Abordagem**: Separação em 3 domínios: *Engagement Loop* (Jogos), *Economy Layer* (Coins/Streaks) e *Transition Engine* (Climax).
- **Ferramenta**: Mermaid.js e SysML (opcional para fluxos complexos).

### 5.4 Design Solution (Definição da Solução)
- **Stack Tecnológica**: Node.js (Backend), React (Frontend), Playwright (OG Image Engine), PostgreSQL (DB).
- **Arquitetura**: Event-driven architecture para o momento "Dia Zero".

---

## 🛠️ 2. Processos de Realização do Produto (5.5 - 5.9)

### 5.5 Product Implementation (Implementação)
- **Abordagem**: Desenvolvimento Modular.
- **Ferramenta**: Docker para isolamento de ambiente (DooD para ferramentas de suporte).
- **Padrão**: [[Padrão de Documentação Agêntica Local]].

### 5.6 Product Integration (Integração)
- **Método**: Integração contínua (CI) de módulos de Frontend e Backend via Docker-compose.
- **Foco**: Sincronização entre o `AI Engine` (Fact or Fiction) e o `Media Repository`.

### 5.7 Product Verification (Verificação)
- **Método**: "Did we build it right?".
- **Atividade**: Veja a [[Matriz de V&V - Birthday Counter]]. Testes unitários (Jest), Testes de Integração e E2E (Cypress).
- **Métrica**: Cobertura de código > 80%.

### 5.8 Product Validation (Validação)
- **Método**: "Did we build the right thing?".
- **Atividade**: Conforme a [[Matriz de V&V - Birthday Counter]], realizar Alpha testing com um grupo de 5 "Sponsors". Verificação do *Viral Loop* e retenção.

---

## 📊 3. Processos de Gerenciamento Técnico (5.10 - 5.17)

### 5.11 Requirements Management (Gestão de Requisitos)
- **Método**: Rastreabilidade entre commits e Git Issues vinculados ao PRD.

### 5.13 Technical Risk Management (Gestão de Risco)
- **Método**: Identificação e mitigação via [[Registro de Riscos - Birthday Counter]].
- **Risco Identificado**: Latência no WebSocket durante o pico de usuários (Climax).
- **Mitigação**: Testes de carga com 10k conexões simuladas antes da Fase D.

### 5.16 Technical Assessment (Avaliação Técnica)
- **Métricas de Performance (TPMs)**:
  - Tempo de resposta da IA (Fact or Fiction) < 2s.
  - Taxa de conversão Sponsor -> Host (Sucesso do Funil).

### 5.17 Decision Analysis (Análise de Decisão)
- **Trade-off**: Playwright vs. Server-side Canvas para geração de OG Images.
- **Resultado**: Escolha por Playwright devido à fidelidade de CSS, apesar do maior overhead de RAM.

---

## 💡 Tailoring aplicado
Para este projeto, os processos de **Fase E (Operações)** e **Fase F (Encerramento)** foram simplificados, focando em CI/CD automatizado e arquivamento de dados (Cápsula do Tempo) após o evento.

---
*Conexões: [[Plano de Gerenciamento de Engenharia de Sistemas (SEMP)]], [[NASA SE Engine]], [[birthday_counter]]*
