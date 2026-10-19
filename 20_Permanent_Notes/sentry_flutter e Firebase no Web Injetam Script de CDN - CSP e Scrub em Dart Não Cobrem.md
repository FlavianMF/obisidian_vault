---
title: sentry_flutter e Firebase no Web Injetam Script de CDN - CSP e Scrub em Dart Não Cobrem
type: trap
tags: [sentry, csp, lgpd, flutter-web, firebase-analytics]
created: 2026-10-19
provenance: outlet_promo
project: outlet_promo
seen_in: [outlet_promo]
verified: 2026-10-19 via leitura do código dos SDKs (sentry_flutter 9.30.1 web_sdk_integration.dart; firebase_core_web 3.12.0); CSP ainda não validada com config real em staging
confidence: low
scope: global
---

# sentry_flutter e Firebase no Web Injetam Script de CDN - CSP e Scrub em Dart Não Cobrem

## Armadilha 1: o CSP precisa liberar scripts que o app não declara

No Web, `sentry_flutter` 9.30.x (`WebSdkIntegration`) injeta
`https://browser.sentry-cdn.com/<versão>/bundle.tracing.min.js` (com SRI) quando
`autoInitializeNativeSdk` é `true` (o padrão). O relatório da fase anterior, escrito a partir do
DSN e do ingest, **não citava** esse host: um CSP montado só dele bloquearia o SDK.

Origens que o CSP de uma app Flutter Web com Firebase + Sentry precisou:

| Origem | Por quê |
|---|---|
| `script-src https://browser.sentry-cdn.com` | bundle JS do Sentry (acima) |
| `script-src https://www.gstatic.com` | `firebase_core_web` carrega `https://www.gstatic.com/firebasejs/<v>/firebase-*.js`; também o CanvasKit |
| `script-src https://www.googletagmanager.com` | Analytics carrega o gtag |
| `script-src 'wasm-unsafe-eval'` | o engine do Flutter Web compila WebAssembly |
| `style-src 'unsafe-inline'` | o engine injeta elementos `<style>` |
| `connect-src https://*.sentry.io` (ingest) e os do Firebase/Analytics | envio de eventos |

Dá para não abrir `script-src` para o Sentry desligando `autoInitializeNativeSdk` no Web, mas
isso muda o que o SDK captura (próxima armadilha).

## Armadilha 2: o JS do Sentry captura erro sem passar pelo scrub em Dart

O bundle injetado captura erros JS por conta própria: esses eventos **não passam por
`beforeSend`** nem pelo scrub de dados pessoais escrito em Dart. Em app sujeito à LGPD, isso
reabre um caminho de vazamento que a camada de observabilidade em Dart já fechava. No
outlet_promo ficou registrado como risco aceito e follow-up: avaliar
`autoInitializeNativeSdk = false` no Web (mexe em dependências e fica fora da fase).

## O que NÃO funcionou

Nada rodou em staging ainda. O que o plano evitou: derivar o CSP do relatório da fase 4 (omitia
`browser.sentry-cdn.com`); a lista final veio do **código dos SDKs**, e a verificação é console
limpo no local mais checagem no checklist de staging. Analytics só liga numa fase posterior.

## Conexões
- [[Firebase Hosting no GitHub Actions - action-hosting-deploy e firebase.json Têm Armadilhas]]
- [[Flutter Web 3.47 - flutter_service_worker.js É Stub, PWA Precisa de Service Worker Próprio]]
