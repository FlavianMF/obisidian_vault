---
title: Lighthouse Não Tem Mais Categoria PWA - Instalabilidade Se Prova por CDP
type: trap
tags: [lighthouse, pwa, installability, chrome-devtools-protocol, playwright]
created: 2026-10-19
provenance: outlet_promo
project: outlet_promo
seen_in: [outlet_promo]
verified: 2026-10-19 via blog do Chrome "Revisiting Chrome's installability criteria" e web.dev/install-criteria (plano da fase 6 do outlet_promo; método CDP ainda não executado)
confidence: low
scope: global
---

# Lighthouse Não Tem Mais Categoria PWA - Instalabilidade Se Prova por CDP

## Armadilha

Critério de aceite escrito como "Lighthouse PWA verde / instalável" não é mais verificável: o
Chrome **removeu a categoria PWA do Lighthouse** (blog do Chrome, *Revisiting Chrome's
installability criteria*). Além disso, o **service worker deixou de ser exigido** para instalar
pelo menu: desde o Chrome 108 (mobile) e 112 (desktop). O prompt de instalação automático
ainda pedia um handler de `fetch` no SW.

Critérios atuais (web.dev/articles/install-criteria): manifest com `name`/`short_name`,
ícones 192 e 512, `start_url`, `display` standalone (ou equivalente),
`prefer_related_applications` falso, HTTPS.

## Como provar "instalável"

- **DevTools › Application › Manifest**, seção *Installability*: lista cada erro.
- **CDP `Page.getInstallabilityErrors`** devolvendo lista vazia. Dá para rodar sem DevTools
  aberto via Playwright (`context.newCDPSession(page)`), então cabe num script/teste de browser.

Registre no relatório que o meio de prova mudou; não reescreva o texto do critério de aceite sem
o dono do PRD.

## O que NÃO funcionou

Nada executado ainda. Descartado no planejamento: (a) usar a nota de PWA do Lighthouse como
prova (a categoria não existe mais); (b) tratar a presença de SW como prova de instalabilidade
(ele não é requisito do menu "Instalar" nas versões atuais).

## Conexões
- [[Flutter Web 3.47 - flutter_service_worker.js É Stub, PWA Precisa de Service Worker Próprio]]
