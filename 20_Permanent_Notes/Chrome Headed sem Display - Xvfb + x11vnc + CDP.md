---
title: Chrome Headed sem Display - Xvfb + x11vnc + CDP
type: pattern
tags: [chrome, cdp, xvfb, vnc, x11vnc, figma, headless, ssh]
created: 2026-10-01
provenance: residencia_cariri_projects
---

# Chrome Headed sem Display - Xvfb + x11vnc + CDP

Chrome headless é inútil para Figma (403 ou muro de login). Em máquina sem display, rode
Chrome **com janela** num display virtual e deixe o usuário logar uma vez por VNC.

## Receita

```bash
Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp
x11vnc -display :99 -localhost -nopw -forever -shared -rfbport 5900
DISPLAY=:99 google-chrome --remote-debugging-port=9222 --user-data-dir=<perfil persistente> \
  --no-first-run --ignore-gpu-blocklist --use-angle=swiftshader --enable-unsafe-swiftshader \
  --window-size=1920,1080
```

- Login único: túnel `ssh -L 5900:localhost:5900 <host>` + cliente VNC em localhost:5900.
  O login persiste no diretório do perfil. VNC só em localhost (sem senha) por segurança.
- Instalação exige sudo (`apt install xvfb x11vnc` + .deb do google-chrome); o agente não tem.

## Armadilha: processo morre com a tarefa

Tarefas em background do Claude Code (`run_in_background`) são mortas no limite (~30 min)
e levam Xvfb e Chrome junto. Suba a pilha desacoplada, de dentro de um script
(`setsid nohup ... & disown`), como `cdp/chrome-up.sh`.

Ver [[Figma Plugin API via CDP no Chrome Logado - Contorna Cota do MCP]],
[[Print de Board Figma Logado via Chrome WSLg + CDP]],
[[Chrome Headless em WSL2 - .deb Oficial, Não apt chromium]].
