---
title: Empacotar App GUI Headless + Servidor MCP numa Única Imagem Docker
type: pattern
tags: [docker, mcp, xvfb, headless, packaging]
created: 2026-08-11
provenance: capella_mcp
---

# Empacotar App GUI Headless + Servidor MCP numa Única Imagem Docker

Quando um servidor MCP precisa driblar uma ferramenta desktop/GUI pesada
que só expõe automação via linha de comando com display virtual (ex.: IDEs
Eclipse-based, ferramentas CAD/MBSE), empacotar tudo — runtime da
ferramenta, `Xvfb`/`xvfb-run`, e o servidor MCP — numa única imagem Docker
resolve dois problemas de uma vez: reprodutibilidade do ambiente (a
ferramenta pesada não precisa ser instalada manualmente em cada máquina) e
transporte MCP (o cliente invoca `docker run -i --rm <imagem>` e fala MCP
por stdio direto do container).

**Quando usar**: a ferramenta-alvo (a) não tem SDK importável fora do seu
próprio processo (ver [[Addons de Scripting Eclipse (EASE) Não São
Pip-Instaláveis]]), e (b) exige GUI/window manager mesmo em modo linha de
comando.

**Como**: uma imagem só, sem Docker-in-Docker — o bridge do servidor MCP
roda `xvfb-run -a <comando-headless>` como subprocess dentro do próprio
container onde o servidor já está rodando. Dados de entrada/saída (modelos,
arquivos) entram via bind mount, não copiados pra dentro da imagem.

**Tradeoff aceito**: latência por chamada (a ferramenta pesada sobe do zero
a cada invocação, se não houver processo persistente) — aceitável quando
simplicidade/desacoplamento pesa mais que performance.

Caso concreto: servidor MCP para Capella (python4capella).

## 🔗 Conexões
- [[Capella MBSE]]
- [[Addons de Scripting Eclipse (EASE) Não São Pip-Instaláveis]]
