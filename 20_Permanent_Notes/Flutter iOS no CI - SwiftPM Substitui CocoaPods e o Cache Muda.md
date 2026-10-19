---
title: Flutter iOS no CI - SwiftPM Substitui CocoaPods e o Cache Muda
type: pattern
tags: [flutter-ios, swiftpm, macos-runner, xcode, ci-cache]
created: 2026-10-19
provenance: outlet_promo
project: outlet_promo
seen_in: [outlet_promo]
verified: 2026-10-19 via flutter.dev/blog/whats-new-in-flutter-3-47, runner-images e Package.swift dos plugins do repo (plano da fase 6 do outlet_promo, 2026-10); build iOS em CI ainda não executado
confidence: low
scope: global
---

# Flutter iOS no CI - SwiftPM Substitui CocoaPods e o Cache Muda

Estado em 2026-10 (reverifique: muda a cada release do Flutter/Xcode).

- **Flutter 3.44+**: Swift Package Manager é o padrão no iOS. Se todos os plugins têm
  `Package.swift` (no outlet_promo: `firebase_core` 4.x, `firebase_analytics` 12.x,
  `sentry_flutter` 9.30), **não há Podfile nem CocoaPods**; o projeto usa
  `FlutterGeneratedPluginSwiftPackage`.
- No job macOS, **cacheie o SwiftPM** em `~/Library/Caches/org.swift.swiftpm` (chave por
  `hashFiles('pubspec.lock')`), não `Pods/`. Mantenha o cache do CocoaPods só atrás de
  `if: hashFiles('apps/consumer/ios/Podfile.lock') != ''`, para virar no-op enquanto não houver
  Podfile e voltar sozinho se um plugin sem SwiftPM entrar.
- A resolução do SwiftPM do Firebase é lenta no primeiro build: `timeout-minutes: 45`.
- **Flutter 3.47**: mínimo iOS 15. **iOS 27 SDK / Xcode 27 exigem UIScene** (`SceneDelegate`).
- Runner: `macos-latest` = `macos-26` (Xcode padrão 26.6 em 2026-10); Xcode 27 ainda em preview.
  Fixe `macos-26` em vez de `latest` para o build não mudar de Xcode sozinho.
- Custo: Linux 2-core US$ 0,006/min, macOS US$ 0,062/min (~10x). Em repo privado Free são 2.000
  min incluídos. Rode iOS só em `master`/release, não em todo PR, e decida se o job iOS bloqueia o
  deploy Web (no outlet_promo, não: roda em paralelo e pode deixar o workflow vermelho sem segurar
  o staging).

## O que NÃO funcionou

Nada foi executado ainda. Descartado por leitura do repo: o passo de cache de `Pods/` e
`pod install` que tutoriais antigos de CI Flutter iOS trazem seria código morto aqui.

## Conexões
- [[Reusar CI como Portão de Deploy com workflow_call, Não workflow_run]]
