---
title: Firebase Hosting no GitHub Actions - action-hosting-deploy e firebase.json Têm Armadilhas
type: trap
tags: [firebase-hosting, hosting-deploy, service-account, well-known, spa-rewrite]
created: 2026-10-19
provenance: outlet_promo
project: outlet_promo
seen_in: [outlet_promo]
verified: 2026-10-19 via README/docs da FirebaseExtended/action-hosting-deploy v0.11.0 e FAQ do Flutter Web (plano da fase 6 do outlet_promo); ainda não executado contra projeto Firebase real
confidence: low
scope: global
---

# Firebase Hosting no GitHub Actions - action-hosting-deploy e firebase.json Têm Armadilhas

## `FirebaseExtended/action-hosting-deploy` (v0.11.0, Node 24, SHA `500ac625ca2dd40cbd15f7659af953801858032a`, 2026-06-25)

- **`firebaseServiceAccount` (JSON da service account) é obrigatório**: não há Workload Identity
  Federation. O secret é uma chave de longa duração; escopo mínimo da SA: *Firebase Hosting Admin*
  e *API Keys Viewer* (Cloud Run Viewer e Firebase Authentication Admin só se houver rewrite para
  Cloud Run / Firebase Auth).
- Em **PR**, a action cria um *check run* "Deploy Preview" e comenta as URLs: o job precisa de
  `checks: write` e `pull-requests: write` (mais `contents: read`). Com `permissions: {}` por
  padrão no topo, declare-as no job.
- **Sem `target`, publica todos os targets** do `firebase.json` (útil para app + admin; perigoso
  se você queria um só).
- `channelId` padrão em PR é `pr<N>-<branch[0:20]>`; defina `channelId: pr-<N>` para URL
  previsível e `expires: 7d`. Saída `urls` é JSON (parse com `jq`).
- `firebaseToolsVersion` fixa a versão do `firebase-tools` (leia do Dockerfile de dev para casar
  local e CI). Referencie a action por SHA.
- Nunca `pull_request_target`; PR de fork não tem secrets: pule o job
  (`github.event.pull_request.head.repo.full_name == github.repository`).

## `firebase.json`

- **`ignore: ["**/.*"]` (template padrão) esconde `/.well-known/`**, onde ficam `assetlinks.json`
  (Android App Links) e `apple-app-site-association` (iOS Universal Links). Use ignores
  explícitos: `[".last_build_id", "**/.DS_Store", "**/node_modules/**"]`.
- **Rewrite de SPA** `** → /index.html` faz `/assets/nao-existe.png` devolver 200 com HTML. Exclua
  o que deve dar 404 de verdade (FAQ do Flutter Web):
  `!(/assets/**|/canvaskit/**|/icons/**|/.well-known/**|/main.dart.*)`.
- **Cache padrão do Hosting é `max-age=3600`**: defina `Cache-Control: no-cache` em `**` quando
  os arquivos não têm hash (ver
  [[Flutter Web 3.47 - flutter_service_worker.js É Stub, PWA Precisa de Service Worker Próprio]]).
- Um app que **não** deve ser PWA/indexado (ex.: painel admin): sem `<link rel="manifest">`, sem
  `manifest.json` publicado (rewrite devolve 404) e `X-Robots-Tag: noindex, nofollow` como prova.

## O que NÃO funcionou

Nada executado ainda. Descartado por leitura de doc: confiar no `ignore` padrão (esconde
`.well-known`), no rewrite padrão de SPA (mascara 404) e no cache padrão de 1 h para build
sem hash. Um smoke de hosting que cheque esses headers/status é parte do plano.

## Conexões
- [[sentry_flutter e Firebase no Web Injetam Script de CDN - CSP e Scrub em Dart Não Cobrem]]
- [[Reusar CI como Portão de Deploy com workflow_call, Não workflow_run]]
