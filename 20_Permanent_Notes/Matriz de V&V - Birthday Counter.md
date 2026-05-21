---
title: Matriz de Verificação e Validação (V&V) - Birthday Counter
type: concept
tags: [systems-engineering, verification, validation, birthday_counter, semp]
created: 2026-05-21
---

# ✅ Matriz de Verificação e Validação (V&V Matrix)

Esta matriz mapeia os requisitos do [[PRD]] para os métodos de prova, garantindo a conformidade técnica (Verificação - 5.7) e a satisfação do usuário (Validação - 5.8).

## 🧪 Métodos de Prova
- **I (Inspeção):** Exame visual da documentação ou código.
- **A (Análise):** Uso de modelos, simulações ou cálculos (ex: Performance).
- **D (Demonstração):** Operação do sistema para mostrar que o requisito funciona.
- **T (Teste):** Execução formal com inputs controlados e resultados esperados.

## 📊 Matriz V&V

| ID Req | Descrição do Requisito | Método | Fase | Critério de Sucesso |
| :--- | :--- | :--- | :--- | :--- |
| **RQ-01** | Transição para `CLIMAX` em < 100ms. | T | Fase D | Log de servidor mostra delta entre cron trigger e websocket emit. |
| **RQ-02** | Geração de 2 verdades e 1 mentira via IA. | T | Fase C | Teste automatizado valida estrutura do JSON e unicidade das strings. |
| **RQ-03** | Cálculo de score Geoguessr via Haversine. | T | Fase C | Teste unitário valida cálculo contra valores de referência conhecidos. |
| **RQ-04** | Idempotência em transações de Coins. | T | Fase D | Envio de `request_id` duplicado resulta em apenas uma transação no DB. |
| **VAL-01** | O usuário se sente engajado pelo ranking social. | D | Fase D | Teste Beta com 5 usuários: >80% de interação com o ranking. |
| **VAL-02** | O "minuto zero" gera o impacto emocional desejado. | D | Fase E | Feedback qualitativo dos stakeholders (Sponsor/Host). |

## 🔗 Rastreabilidade
Esta matriz deve ser atualizada sempre que o [[PRD]] sofrer alterações, garantindo que nenhum requisito fique sem uma estratégia de teste correspondente.

---
*Referência: [[NASA SE Engine]], [[Detalhamento dos Processos Técnicos no SEMP]]*
