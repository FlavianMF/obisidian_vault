---
title: flutter create deriva o bundle ID de --org + --project-name
type: trap
tags: [trap, flv]
created: 2026-11-09
provenance: flv
seen_in: [flv]
confidence: low
scope: global
verified: 2026-11-09 via candidato do agente em flv, não reproduzido na revisão
---

# flutter create deriva o bundle ID de --org + --project-name

## Contexto
flutter create --org br.com.x --project-name consumer gera applicationId/namespace/PRODUCT_BUNDLE_IDENTIFIER br.com.x.consumer. Para outro ID (ex.: br.com.x.app) editar build.gradle.kts (namespace e applicationId), mover MainActivity.kt e trocar o package, e sed no project.pbxproj. namespace diferente do package do MainActivity compila mas quebra ao abrir.

## O que NÃO funcionou
- A preencher
