---
title: Gradle daemon morre em host de 8 GB com flutter em paralelo
type: trap
tags: [trap, outlet_promo]
created: 2026-10-30
provenance: outlet_promo
seen_in: [outlet_promo]
confidence: low
scope: global
verified: 2026-10-30 via candidato do agente em outlet_promo, não reproduzido na revisão
---

# Gradle daemon morre em host de 8 GB com flutter em paralelo

## Contexto
flutter build apk em paralelo com make check (analyze/test) mata o daemon: 'Gradle build daemon disappeared unexpectedly'. O Claude Code também encerra shell em background sob pressão de memória. Rodar o APK sozinho, sem outra carga, e checar free -m antes.

## O que NÃO funcionou
- A preencher
