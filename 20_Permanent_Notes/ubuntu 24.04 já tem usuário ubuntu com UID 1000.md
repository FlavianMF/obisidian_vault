---
title: ubuntu:24.04 já tem usuário ubuntu com UID 1000
type: trap
tags: [trap, outlet_promo]
created: 2026-10-30
provenance: outlet_promo
seen_in: [outlet_promo]
confidence: low
scope: global
verified: 2026-10-30 via candidato do agente em outlet_promo, não reproduzido na revisão
---

# ubuntu:24.04 já tem usuário ubuntu com UID 1000

## Contexto
A imagem oficial ubuntu:24.04 traz o usuário ubuntu (UID/GID 1000). Criar um usuário dev com o UID do host falha ou colide; rode userdel --remove ubuntu antes do useradd.

## O que NÃO funcionou
- A preencher
