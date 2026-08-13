---
title: Eclipse SWT Browser Quebra em Ubuntu 24.04+ Sem libwebkit2gtk-4.1
type: trap
tags: [eclipse, swt, rcp, gtk, webkit, ubuntu, linux]
created: 2026-08-13
provenance: capella_mcp
project: capella_mcp
---

# Eclipse SWT Browser Quebra em Ubuntu 24.04+ Sem libwebkit2gtk-4.1

## Sintoma

Abrir uma view/editor Eclipse RCP que usa o widget `org.eclipse.swt.browser.Browser`
(editor de descrição rich-text, Welcome/Intro, qualquer painel HTML
embutido) em Ubuntu 24.04 (noble) lança:

```
Unhandled event loop exception
No more handles because there is no underlying browser available.
Please ensure that WebKit with its GTK 3.x/4.x bindings is installed.
```

Confirmado abrindo um projeto no Capella 7.1.0 (GUI local, fora do
Docker) — nada a ver com o conteúdo do projeto/modelo em si.

## Causa

`Browser` do SWT em Linux é implementado sobre WebKitGTK. Ubuntu 24.04
removeu `libwebkit2gtk-4.0` dos repositórios (só ficou disponível
`4.1`). Se a instalação não tem nenhuma das duas, o widget falha ao
inicializar — mas Eclipse/SWT versões usadas por Capella 7.1.0 já sabem
usar o binding `4.1` como fallback, então **não é preciso a lib antiga
(indisponível de qualquer forma)**.

## Fix

```
sudo apt install libwebkit2gtk-4.1-0
```

Reabrir o app depois — sem precisar reinstalar/reconfigurar nada do
Eclipse/produto em si.

## Generalização

Qualquer app Eclipse RCP (não só Capella) rodando GUI em Ubuntu
22.04+/24.04+ pode bater nisso na primeira vez que algo abre um widget
`Browser`. Sintoma idêntico independe do produto — o fix é sempre
"instalar o pacote webkit2gtk que a distro realmente tem disponível",
não necessariamente o nome exato mencionado em mensagens de erro/doc
mais antigas (`4.0`).

## 🔗 Conexões
- [[Addons de Scripting Eclipse (EASE) Não São Pip-Instaláveis]]
- [[Capella MBSE]]
