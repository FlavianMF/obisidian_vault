---
title: Registro de Riscos Técnicos - Birthday Counter
type: concept
tags: [systems-engineering, risk-management, birthday_counter, semp]
created: 2026-05-21
---

# ⚠️ Registro de Riscos Técnicos (Technical Risk Register)

Este documento identifica os riscos técnicos críticos para o projeto **Birthday Counter** e define estratégias de mitigação, conforme exigido pelo processo **5.13 (Technical Risk Management)** do SEMP.

## 📋 Matriz de Riscos

| ID | Risco Técnico | Probabilidade | Impacto | Estratégia de Mitigação |
| :--- | :--- | :--- | :--- | :--- |
| **RT-01** | Latência excessiva no WebSocket durante o `CELEBRATION_TRIGGER`. | Média | Crítico | Implementar Redis Pub/Sub para escalabilidade e realizar testes de carga (10k+ conexões). |
| **RT-02** | Falha ou alucinação da IA na geração do "Fact or Fiction". | Alta | Médio | Implementar validação sintática via Pydantic e um fallback de "quizzes pré-escritos" caso a API falhe. |
| **RT-03** | Consumo excessivo de RAM pelo Playwright (OG Image Engine). | Alta | Médio | Usar uma fila de processamento (Celery/BullMQ) para limitar o número de instâncias simultâneas do browser. |
| **RT-04** | Exposição de dados sensíveis em metadados de fotos (GPS/EXIF). | Média | Alto | Implementar um middleware de sanitização que remove metadados sensíveis no upload, mantendo apenas o necessário para os jogos. |
| **RT-05** | Rate Limit em APIs externas (Spotify/Google Maps). | Média | Médio | Implementar cache agressivo de respostas e um sistema de monitoramento de cotas com alertas. |

## 🔄 Monitoramento
Os riscos devem ser revisados quinzenalmente durante o **Technical Assessment (5.16)**. Novos riscos identificados durante o desenvolvimento devem ser adicionados imediatamente.

---
*Referência: [[Plano de Gerenciamento de Engenharia de Sistemas (SEMP)]]*
