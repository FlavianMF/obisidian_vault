---
title: 🗺️ Cheat Sheet: Ciclo de Vida SE Completo
type: template
tags: []
created: 2026-05-21
provenance: manual
---

# 🗺️ Cheat Sheet: Ciclo de Vida SE Completo

Resumo visual das fases NASA/INCOSE para consulta rápida durante estudos.

## 🚀 Linha do Tempo de Fases (NASA)

```mermaid
gantt
    title Ciclo de Vida do Projeto
    dateFormat  YYYY-MM-DD
    section Formulação
    Pré-Fase A (Conceito) :a1, 2026-01-01, 30d
    Fase A (Desenvolvimento) :a2, after a1, 45d
    Fase B (Definição) :a3, after a2, 60d
    section Implementação
    Fase C (Design Final) :b1, after a3, 90d
    Fase D (AI&T / Lançamento) :b2, after b1, 60d
    Fase E (Operações) :b3, after b2, 120d
    Fase F (Encerramento) :b4, after b3, 30d
```

## 📐 O V-Model Simplificado
- **Esquerda (Decomposição)**: O que queremos? → Como faremos?
- **Base (Construção)**: Fazer o produto.
- **Direita (Integração)**: Funciona? (Verificação) → Resolve o problema? (Validação)

## ⚖️ Critérios de Trade-off
Sempre que houver duas soluções, compare:
1. **Performance** (Atende o requisito?)
2. **Custo** (Cabe no orçamento?)
3. **Risco** (Conseguimos fazer a tempo?)
4. **Massa/Energia** (Restrições físicas)

## 🔗 Links Úteis
- [[V-Model (Vee Model)]]
- [[Análise de Trade-off (Trade Study)]]
- [[Fases de Implementação e Encerramento (C-F)]]
