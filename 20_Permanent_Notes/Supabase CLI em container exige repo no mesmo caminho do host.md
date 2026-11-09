---
title: Supabase CLI em container exige repo no mesmo caminho do host
type: trap
tags: [trap, outlet_promo]
created: 2026-11-09
provenance: outlet_promo
seen_in: [outlet_promo]
confidence: low
scope: global
verified: 2026-11-09 via candidato do agente em outlet_promo, não reproduzido na revisão
---

# Supabase CLI em container exige repo no mesmo caminho do host

## Contexto
Num dev container com o socket do Docker do host, supabase start cria containers irmãos e monta pastas do projeto pelo caminho do host. Monte o repo como ${PROJECT_DIR}:${PROJECT_DIR} e use working_dir igual; com /workspace ou outro caminho, os bind mounts quebram.

## O que NÃO funcionou
- A preencher
