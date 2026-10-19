---
title: Flutter Web 3.47 - flutter_service_worker.js É Stub, PWA Precisa de Service Worker Próprio
type: trap
tags: [flutter, flutter-web, pwa, service-worker, cache, sw-design]
created: 2026-10-19
provenance: outlet_promo
project: outlet_promo
seen_in: [outlet_promo]
verified: 2026-10-19 via build local do Flutter 3.47.6 e FAQ oficial do Flutter Web; desenho do SW no plano da fase 6 do outlet_promo (Task 6), ainda sem teste A/B em navegador nem publicação em staging
confidence: low
scope: global
---

# Flutter Web 3.47 - flutter_service_worker.js É Stub, PWA Precisa de Service Worker Próprio

## Armadilha

Quem espera que `flutter build web` entregue um PWA com cache offline (como nas versões
antigas) não recebe nada disso. O build ainda gera `build/web/flutter_service_worker.js`, mas
ele é um **stub de limpeza**: no evento `activate` faz `registration.unregister()` e
`client.navigate()` em **todas as abas** abertas. O `flutter_bootstrap.js` padrão ainda o
registra via `serviceWorkerSettings`. Resultado: o SW se instala, se apaga e recarrega a aba.

Doc oficial (FAQ do Flutter Web): *"Flutter no longer generates or manages a caching service
worker by default"*. Conferido no build 3.47.6.

## Consequências

- **Bootstrap customizado**: `web/flutter_bootstrap.js` com `{{flutter_js}}`,
  `{{flutter_build_config}}` e `_flutter.loader.load();` **sem** `serviceWorkerSettings`. Sem essa
  chave o loader não registra SW nenhum.
- **App Web que NÃO é PWA também precisa do bootstrap customizado.** O padrão registraria o stub,
  que recarrega a aba na primeira visita (no outlet_promo, o app admin). Remova também o
  `flutter_service_worker.js` do `build/web` no script de build.
- **Cache longo quebra atualização.** O Flutter não põe hash nos nomes (`main.dart.js`,
  `canvaskit/`, `assets/`, `flutter_bootstrap.js`), então "cache longo para assets com hash" não se
  aplica: use `Cache-Control: no-cache` em tudo (revalida por ETag, recebe 304). O CanvasKit vem de
  `www.gstatic.com/flutter-canvaskit/<engineRevision>/`, caminho versionado, com cache longo do
  próprio Google. **Firebase Hosting usa `max-age=3600` por padrão**: sem header explícito, uma
  versão nova demora até 1 h (ver
  [[Firebase Hosting no GitHub Actions - action-hosting-deploy e firebase.json Têm Armadilhas]]).

## O que fazer: SW mínimo, para instalar e nunca prender o usuário numa versão velha

**Fetch** (só `GET`):

- **Mesma origem (o shell): rede primeiro**; guarda cópia se `ok`; sem rede, cai no cache. Cache
  primeiro serviria `main.dart.js` antigo, porque os nomes não mudam.
- **Cache primeiro só para CDN versionado**: `https://www.gstatic.com/flutter-canvaskit/<engineRevision>/`
  e `https://fonts.gstatic.com/`.
- **Todo o resto passa direto, sem `respondWith`** (Supabase, Firebase, Sentry). Não cachear
  resposta cross-origin fora do gstatic.
- Cache nomeado com o `BUILD_ID`; `activate` apaga caches antigos do mesmo prefixo e faz
  `clients.claim()`. `install` **não** chama `skipWaiting` (a troca é pedida pelo usuário).

**Detectar versão nova**:

- Carimbar `BUILD_ID` no `sw.js` **depois do build**: placeholder `__BUILD_ID__` trocado por 16 hex
  do sha256 dos arquivos de `build/web` (exceto o `sw.js`). O carimbo tem que mudar a cada build
  diferente; se o `sw.js` ficasse byte a byte igual, o navegador nunca veria SW novo e o aviso não
  apareceria. O script de build deve falhar se o placeholder não existir.
- `navigator.serviceWorker.register('sw.js', { updateViaCache: 'none' })` no `load`.
- Aviso "nova versão": worker novo em `installed` **com `controller` presente** (sem controller é
  a primeira instalação) ou `registration.waiting` já existente.
- `registration.update()` ao voltar à aba (`visibilitychange`) e a cada hora.
- Aplicar: `postMessage({type: 'SKIP_WAITING'})` ao worker em espera e reload no `controllerchange`.

A garantia de atualização vem de **duas coisas, não do aviso**: `Cache-Control: no-cache` no
hosting e rede primeiro no SW; um reload comum, mesmo com SW antigo no controle, já busca tudo da
rede. Com CSP `script-src 'self'`, o `index.html` não pode ter script inline: a ponte JS vai em
arquivo próprio.

## O que NÃO funcionou

Nada foi executado em produção: o achado vem de ler o build real (3.47.6) e a FAQ oficial no
planejamento. Descartado por esse motivo: confiar no `flutter build web` + bootstrap padrão para
ter PWA/offline (o SW gerado se desregistra); cache longo nos arquivos do build por analogia com
assets com hash (nomes fixos, usuário preso numa versão velha); cache primeiro para o shell.
O desenho do SW acima ainda não passou por teste A/B de dois builds.

## Conexões
- [[Lighthouse Não Tem Mais Categoria PWA - Instalabilidade Se Prova por CDP]]
- [[sentry_flutter e Firebase no Web Injetam Script de CDN - CSP e Scrub em Dart Não Cobrem]]
