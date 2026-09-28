---
title: Print de Board Figma Logado via Chrome WSLg + CDP
type: trap
tags: [figma, figjam, chrome, cdp, wsl, screenshot, headless]
created: 2026-09-28
provenance: residencia_00
---

# Print de Board Figma Logado via Chrome WSLg + CDP

Quando o usuário veta as ferramentas de leitura do MCP do Figma (`get_figjam`,
`get_screenshot`) e pede "print pelo Chrome", `google-chrome --headless --screenshot`
**não serve**:

- UA `HeadlessChrome` → **403 do CloudFront** do figma.com.
- Com UA de navegador normal → tela "Sign up or Log in" (board não é público).
- Chrome WSLg sem flags → `WebGL1 blocklisted`; o canvas do Figma não renderiza.

## O que funciona

```bash
google-chrome --remote-debugging-port=9222 \
  --user-data-dir=$JOB_TMP/chrome-profile --no-first-run \
  --ignore-gpu-blocklist --use-angle=swiftshader --enable-unsafe-swiftshader \
  "<url do board>"
```

1. Janela abre no WSLg; o **usuário loga uma vez** no perfil isolado (não mexe no
   Chrome do Windows).
2. Print: script Node 20 com `node --experimental-websocket`, `fetch('http://127.0.0.1:9222/json')`
   → `Page.captureScreenshot`. Navegar com `Page.navigate` para `?node-id=X-Y` faz o
   Figma dar zoom no nó — serve de "zoom por bloco" sem clicar.
3. Medir geometria/cores: decodificar o PNG em Python stdlib (zlib + filtros PNG) e
   varrer transições de cor numa linha/coluna — dá bbox e hex exatos dos blocos.
   `clip.scale>1` no CDP só faz upscale do bitmap; não melhora leitura de texto
   miúdo.
4. Bônus: a mesma janela logada abre a URL do OAuth do MCP do Figma, e o usuário só
   clica "Allow".

## Armadilha correlata — sticky FigJam tem tamanho fixo

`STICKY` é 240×240 (ou 416 largo), sem `resize()`. Para reconstruir um template de
canvas com stickies, **escale a grade**, não o sticky: fator = o que faz o bloco mais
cheio caber (ali, 11 stickies em Requisitos → 7,2× a medida de tela). Depois ajuste
`sticky.text.fontSize` ao maior valor que mantém `height == 240` (sticky cresce
sozinho se o texto transborda), e unifique pelo mínimo dentro de cada bloco.

Relacionado: [[Chrome Headless em WSL2 - .deb Oficial, Não apt chromium]],
[[Project Model Canvas vs ARCADIA - Mapeamento]].
