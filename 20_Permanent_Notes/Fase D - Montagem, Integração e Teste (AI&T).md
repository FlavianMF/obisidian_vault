---
title: Fase D - Montagem, Integração e Teste (AI&T)
type: concept
tags: [nasa-se, lifecycle, integration, validation, verification]
created: 2026-05-21
provenance: NASA SE Handbook / INCOSE
---

# Fase D - Montagem, Integração e Teste (AI&T)

## 🎯 Objetivo
Montar os subsistemas, integrar o software ao hardware e verificar/validar se o sistema completo funciona conforme o esperado em seu ambiente de operação.

## 🛠️ Atividades Principais
1.  **Integração Progressiva**: Unir os blocos (Pilar 3) um a um, testando as interfaces em cada etapa (Bottom-up Integration).
2.  **Verificação (Verification)**: "Construímos o sistema corretamente?". Testes contra os requisitos técnicos (L1/L2).
3.  **Validação (Validation)**: "Construímos o sistema correto?". Testes contra as necessidades do stakeholder (Pilar 1).
4.  **Testes Ambientais**: Expor o sistema a condições reais (térmico, vibração, EMI/EMC).
5.  **Treinamento de Operadores**: Preparar a equipe que gerenciará o sistema na Fase E.

## 📦 Entregáveis Principais
- **As-Built Configuration**: Documentação do sistema como ele foi realmente construído (diferente do design teórico se houver ajustes de campo).
- **V&V Reports**: Provas documentais de que o sistema passou em todos os testes.
- **Manual de Operação e Manutenção**: Guia para o usuário final.

## 🏁 Gate Review
- **Test Readiness Review (TRR)**: Garante que o sistema e as ferramentas de teste estão prontos para a campanha de V&V.
- **System Acceptance Review (SAR)**: O cliente aceita formalmente o sistema.
- **Operational Readiness Review (ORR)**: Confirma que o sistema, equipe e suporte estão prontos para entrar em operação.

## 🔗 Conexões
- [[Ciclo de Vida de Engenharia de Sistemas]]
- [[Digital Twin]] (Utilizado aqui para comparar o comportamento real vs. simulado)
- [[Framework 3 Pilares SE]] (Validação final do Pilar 3 contra o Pilar 1)
