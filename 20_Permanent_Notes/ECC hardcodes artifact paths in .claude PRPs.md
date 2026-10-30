---
title: ECC hardcodes artifact paths in .claude/PRPs
type: trap
tags: [trap, outlet_promo]
created: 2026-10-30
provenance: outlet_promo
seen_in: [outlet_promo]
confidence: low
scope: global
verified: 2026-10-30 via candidato do agente em outlet_promo, não reproduzido na revisão
---

# ECC hardcodes artifact paths in .claude/PRPs

## Contexto
Comandos do plugin ecc (prp-prd, prp-plan, prp-implement, plan) gravam em .claude/PRPs/* sem config; patchar cache do plugin se perde no update. Solução: regra de projeto em .claude/rules/ecc-artifacts.md redirecionando para docs/. Eficácia da regra textual ainda não testada.

## O que NÃO funcionou
- A preencher
