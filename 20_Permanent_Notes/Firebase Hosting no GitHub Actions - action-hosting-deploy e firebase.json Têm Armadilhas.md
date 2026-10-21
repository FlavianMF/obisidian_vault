---
title: Firebase Hosting no GitHub Actions - action-hosting-deploy e firebase.json Têm Armadilhas
type: trap
tags: [firebase-hosting, hosting-deploy, service-account, well-known, spa-rewrite]
created: 2026-10-19
provenance: outlet_promo
project: outlet_promo
seen_in: [outlet_promo]
verified: 2026-10-21 via run 39619762122 do outlet_promo (deploy real em prod; smoke 404 no 1º run e verde no re-run); antes 2026-10-19 via docs da FirebaseExtended/action-hosting-deploy v0.11.0
confidence: medium
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

## Smoke logo após o deploy dá 404 em site novo

No primeiro deploy `live` de dois sites Hosting recém-criados, o smoke rodou ~0,1 s depois do `firebase deploy`
e recebeu 404 em todas as rotas (`FALHOU consumer /: status 404, esperado 200`). Segundos depois o `curl`
devolvia 200 com todos os headers e `check_hosting.sh` passava. Causa provável (inferida dos timestamps):
a versão ainda não propagou no CDN. O job já tinha publicado migrations e Hosting; só o step de smoke ficou vermelho.
Solução: `gh run rerun <id> --failed`, ou, no workflow, esperar/repetir o smoke algumas vezes antes de falhar.

## O que NÃO funcionou

- Smoke executado imediatamente após o deploy em site novo: 404 (acima). Re-run do job resolveu.
- Descartado por leitura de doc, ainda não exercitado: confiar no `ignore` padrão (esconde
  `.well-known`), no rewrite padrão de SPA (mascara 404) e no cache padrão de 1 h para build
  sem hash. O smoke de headers/status cobre esses pontos e passou em prod.

## Conexões
- [[sentry_flutter e Firebase no Web Injetam Script de CDN - CSP e Scrub em Dart Não Cobrem]]
- [[Reusar CI como Portão de Deploy com workflow_call, Não workflow_run]]
