---
title: Analytics com consentimento LGPD e catálogo tipado
type: pattern
tags: [pattern, outlet_promo]
created: 2026-10-30
provenance: outlet_promo
seen_in: [outlet_promo]
confidence: low
scope: global
verified: 2026-10-30 via candidato do agente em outlet_promo, não reproduzido na revisão
---

# Analytics com consentimento LGPD e catálogo tipado

## Contexto
A coleta do Firebase Analytics começa desligada e só liga após o consentimento de termos. O catálogo inteiro de eventos é definido no PRD de fundação, com PRD dono por evento. Um wrapper tipado e um teste rejeitam evento fora do catálogo e parâmetro com PII (e-mail, telefone, GPS). user_id é o UUID do backend.

## O que NÃO funcionou
- A preencher
