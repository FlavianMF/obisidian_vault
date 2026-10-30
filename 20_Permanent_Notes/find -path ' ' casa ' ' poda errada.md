---
title: find -path '*' casa '/': poda errada
type: trap
tags: [trap, outlet_promo]
created: 2026-10-30
provenance: outlet_promo
seen_in: [outlet_promo]
confidence: low
scope: global
verified: 2026-10-30 via candidato do agente em outlet_promo, não reproduzido na revisão
---

# find -path '*' casa '/': poda errada

## Contexto
Em find, -path './apps/*/build' também casa apps/x/lib/build (o * atravessa /). Usar -regex './apps/[^/]*/build' para podar só o build direto do app. Teste com fixture temporária pegou antes do commit.

## O que NÃO funcionou
- A preencher
