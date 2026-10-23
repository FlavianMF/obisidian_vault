---
title: AdSense Só Suporta CSP Estrito com Nonce - Hosting Estático Não Gera Nonce
type: trap
tags: [adsense, csp, nonce, firebase-hosting, flutter-web, security-headers]
created: 2026-10-23
provenance: outlet_promo
project: outlet_promo
seen_in: [outlet_promo]
verified: 2026-10-23 via leitura de support.google.com/adsense/answer/16283098 e do firebase.json do outlet_promo; nada implementado nem testado em staging
confidence: low
scope: global
---

# AdSense Só Suporta CSP Estrito com Nonce - Hosting Estático Não Gera Nonce

Um site com CSP fechado por lista de domínios não consegue ligar o AdSense só com mais hosts na lista. O Google documenta suporte apenas ao CSP estrito, com nonce por resposta. Um hosting estático, como o Firebase Hosting, serve cabeçalho fixo e não gera nonce.

## A regra do Google

A página "Integrate the AdSense ad code with a Content Security Policy" diz que os domínios do código de anúncio mudam com o tempo. Por isso, o Google só dá suporte ao CSP estrito. O exemplo oficial:

```text
object-src 'none';
script-src 'nonce-{random}' 'unsafe-inline' 'unsafe-eval' 'strict-dynamic' https: http:;
base-uri 'none';
report-uri https://your-report-collector.example.com/
```

- O nonce vai em **toda** tag `<script>` da página, inclusive no código do AdSense.
- A página avisa: "More restrictive policies may break without notice".
- O exemplo pede `'unsafe-eval'`. Um app Flutter Web costuma ter só `'wasm-unsafe-eval'`.

## Por que quebra num app com CSP fechado

O CSP do outlet_promo (Flutter Web PWA no Firebase Hosting) tinha `default-src 'self'`, `script-src` por lista, e `img-src` e `connect-src` fechados. Contra o AdSense, isso falha em três pontos:

1. **Nonce.** O cabeçalho do `firebase.json` é fixo. O nonce exige que o `index.html` saia de uma função (Cloud Functions ou Cloud Run). Isso cria partida a frio no primeiro carregamento.
2. **Iframes.** Sem `frame-src`, o `default-src 'self'` bloqueia os iframes do anúncio.
3. **Beacons e imagens.** O exemplo do Google não restringe `connect-src` nem `img-src`. Na prática, os dois abrem para `https:`. Isso aumenta a superfície de exfiltração do app inteiro, inclusive da sessão do Supabase guardada no navegador.

Efeito colateral no service worker: se o `index.html` passar a ter nonce dinâmico e o SW usar `networkFirst` com cache, o modo offline reusa o nonce antigo. Tire `/` e `/index.html` do cache.

## O que NÃO funcionou

Nada foi implementado. A pesquisa descartou duas saídas no papel:

- **Lista de domínios no CSP:** o Google não dá suporte e avisa que ela quebra sem aviso.
- **Só acrescentar hosts ao CSP atual:** não resolve o nonce nem os iframes.

Uma alternativa ficou sem verificação: isolar o anúncio num iframe de outra origem, com CSP próprio. A compatibilidade dela com a política do AdSense não foi encontrada.

## Conexões
- [[sentry_flutter e Firebase no Web Injetam Script de CDN - CSP e Scrub em Dart Não Cobrem]]
- [[Firebase Hosting no GitHub Actions - action-hosting-deploy e firebase.json Têm Armadilhas]]
- [[Flutter Web 3.47 - flutter_service_worker.js É Stub, PWA Precisa de Service Worker Próprio]]
- [[AdSense em App Flutter Web Atrás de Login - Aprovação Improvável e Pacote Oficial Só para Jogos]]
