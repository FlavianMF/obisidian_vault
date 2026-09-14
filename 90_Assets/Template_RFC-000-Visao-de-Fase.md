---
title: Template_RFC-000-Visao-de-Fase
type: template
tags: [template, rfc, product-decisions, risk]
created: 2026-09-11
provenance: orbita-platform
---

# Template — RFC-000 (visão da fase, `docs/escopo/rfc/`)

Só em projeto de **nível 3**. É o contrato da fase: registra as decisões de produto
numeradas e mapeia as RFCs que as detalham. Ver
[[RFC de Produto - Anatomia e Ciclo de Status]].

```markdown
# RFC-000 — Visão da Fase N: {{title}}

**Status**: Aceito · **Data**: AAAA-MM-DD
**Origem**: [<documento de intenção>](…) + [<escopo do sistema>](…) + [<análise operacional>](…)

---

## 1. Contexto e Estratégia
<!-- O que a fase anterior entregou, que ator/área abre agora, qual é a aposta de negócio. -->

## 2. Decisões de Produto (registradas em AAAA-MM-DD)
<!-- O contrato. Uma linha por decisão, número imutável. Decisão revisada não é reescrita:
     fica "**Revisada**: <nova> (a decisão original era <antiga>; motivo)". -->

| # | Tema | Decisão | RFC |
|---|------|---------|-----|
| D1 |  |  | [RFC-001](./RFC-001-….md) |
| D2 |  |  |  |

## 3. Mapa das RFCs da Fase
| RFC | Título | Domínio |
|-----|--------|---------|
| [RFC-000](./RFC-000-….md) | Visão da Fase (este documento) | Produto |
| [RFC-001](./RFC-001-….md) |  |  |

<!-- O sequenciamento de implementação NÃO fica aqui — fica no plano de fase. -->

## 4. Fora de Escopo desta Fase
<!-- Obrigatória. Cada item com o link para onde ele foi empurrado. -->

## 5. Requisitos Transversais (herdados da governança)
<!-- TDD, piso de cobertura, segurança, identidade visual, ambiente de execução. -->

## 6. Riscos Principais
| Risco | Impacto | Mitigação |
|-------|---------|-----------|
|  | Crítico / Alto / Médio | <!-- a mitigação linka a RFC/§ que a executa --> |

---
**Referências**: …
```

## 🔗 Conexões
- [[RFC de Produto - Anatomia e Ciclo de Status]]
- [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]]
