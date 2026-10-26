---
title: Depurar Login por Link Mágico PKCE em Flutter Web - Navegador sem WebGL Fica em Branco e Cada Pedido Invalida o Link Anterior
type: trap
tags: [flutter-web, supabase-auth, pkce, playwright, canvaskit, debug]
created: 2026-10-26
provenance: outlet_promo
project: outlet_promo
seen_in: [outlet_promo]
verified: 2026-10-26 via depuração do painel admin no preview da PR #20 (navegador embutido do Traycer e Playwright)
confidence: low
scope: global
---

# Depurar Login por Link Mágico PKCE em Flutter Web - Navegador sem WebGL Fica em Branco e Cada Pedido Invalida o Link Anterior

## 1. Navegador sem WebGL deixa o Flutter Web em branco

O navegador embutido do Traycer (Electron) não tinha WebGL. O app Flutter Web, com CanvasKit, ficou em branco:

- Todos os assets voltaram 200, inclusive `canvaskit.wasm` e `main.dart.js`.
- O DOM ficou só com `<script>`, sem `flutter-view`.
- O único log era `Falling back to CPU-only rendering. Reason: webGLVersion is -1`.
- Nenhuma requisição saiu para o backend.

O Playwright com Chromium renderizou o mesmo app. Antes de buscar bug no código, teste se `canvas.getContext('webgl2')` devolve contexto.

## 2. Ler a tela do Flutter pelo Playwright

O Flutter Web só expõe a árvore de acessibilidade depois de ativada:

- O snapshot inicial mostra só o botão "Enable accessibility".
- `click` no botão estourou o tempo: o elemento fica fora da viewport.
- Disparar o clique por `evaluate` funcionou: `document.querySelector('flt-semantics-placeholder').dispatchEvent(new MouseEvent('click', {bubbles: true}))`.
- Depois disso, o snapshot lista `textbox` e `button` com nome, e `type` e `click` funcionam.

## 3. PKCE: o verificador fica no navegador que pediu o link

O link só conclui o login no navegador que fez o `POST /auth/v1/otp`. O Flutter guarda o verificador PKCE nesse navegador.

- Pedir o link no Chrome e abrir o e-mail em outro navegador falha.
- Um novo pedido de link para o mesmo usuário invalida o token anterior. Abrir o link velho devolve `error_code=otp_expired` e "Email link is invalid or has expired".

Para reproduzir com um agente:

1. Peça o link no navegador do agente, com o e-mail do usuário.
2. Peça ao usuário que cole o link do e-mail mais novo, sem clicar nele. O clique consome o token.
3. Abra o link no navegador do agente. O redirect traz `?code=...` e o app faz `POST /auth/v1/token?grant_type=pkce`.

## 4. Segredo na aba de rede

Os cabeçalhos de uma requisição autenticada contêm o `Authorization: Bearer <JWT>` e o `apikey`. Ler os cabeçalhos pela ferramenta de rede imprime a sessão do usuário. Leia o corpo da resposta primeiro, e só leia os cabeçalhos se o diagnóstico exigir. Avise o usuário e sugira encerrar a sessão.

## O que NÃO funcionou

- Abrir o painel no navegador embutido sem WebGL: tela branca, sem erro útil.
- `click` no botão "Enable accessibility" pelo Playwright: falha por elemento fora da viewport.
- Abrir um link mágico pedido em outro navegador, ou já substituído por um pedido novo: `otp_expired`.
