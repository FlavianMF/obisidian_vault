---
title: Feature flags e config avaliadas no Postgres (Supabase)
type: pattern
tags: [pattern, outlet_promo]
created: 2026-10-30
provenance: outlet_promo
seen_in: [outlet_promo]
confidence: low
scope: global
verified: 2026-10-30 via candidato do agente em outlet_promo, não reproduzido na revisão
---

# Feature flags e config avaliadas no Postgres (Supabase)

## Contexto
Flags e config ficam em tabela Supabase. Funções SQL (is_feature_enabled, get_config com override por outlet e fallback global) servem client e Edge Functions, então a regra existe uma vez só. RPC get_my_flags devolve só os booleanos, sem expor allowlists. Uma função user_plan() stub isola o conceito de plano para o futuro. Validação min/max fica no banco e a auditoria por trigger.

## O que NÃO funcionou
- A preencher
