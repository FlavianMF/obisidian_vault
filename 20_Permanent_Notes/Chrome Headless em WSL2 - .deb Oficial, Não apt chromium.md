---
title: Chrome Headless em WSL2 - .deb Oficial, Não apt chromium
type: pattern
tags: [chrome, chromium, headless, wsl2, ubuntu, apt, snap]
created: 2026-09-21
provenance: residencia_00
---

# Chrome Headless em WSL2 - .deb Oficial, Não apt chromium

Em Ubuntu (testado 24.04 sob WSL2), `apt install chromium` /
`chromium-browser` não instala um binário nativo — resolve pro wrapper snap
transicional do Ubuntu. Isso é mais lento no primeiro start e historicamente
dá dor de cabeça com flags headless.

**Como instalar sem snap**: baixar o `.deb` oficial do Google Chrome Stable e
instalar via `apt` (que resolve as dependências):

```bash
wget -O /tmp/google-chrome-stable_current_amd64.deb \
  https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install /tmp/google-chrome-stable_current_amd64.deb
```

Binário fica em `google-chrome`. É também o alvo mais testado por
ferramentas headless (Puppeteer/Playwright/Selenium apontam pra Chrome
Stable por padrão).

**Smoke test headless**:
```bash
google-chrome --headless=new --no-sandbox --disable-gpu --dump-dom https://example.com
```

**Armadilha (cosmética)**: sob WSL2, todo comando headless imprime no stderr:
```
[ERROR:dbus/object_proxy.cc:572] Failed to call method: org.freedesktop.DBus.Properties.GetAll: ... org.freedesktop.UPower was not provided by any .service files
```
Inofensivo — não há serviço DBus/UPower no WSL2. Comando ainda sai com
exit code 0 e output correto. Não tratar como falha.

**`--no-sandbox`** é necessário sob WSL2 pra headless rodar sem setup extra
de sandbox (namespaces/seccomp não totalmente equivalentes a um kernel Linux
nativo).

## 🔗 Conexões
- [[Empacotar App GUI Headless + Servidor MCP numa Única Imagem Docker]]
