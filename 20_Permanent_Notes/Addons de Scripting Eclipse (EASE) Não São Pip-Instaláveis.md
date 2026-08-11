---
title: Addons de Scripting Eclipse (EASE) Não São Pip-Instaláveis
type: trap
tags: [eclipse, ease, py4j, python, rcp]
created: 2026-08-11
provenance: capella_mcp
---

# Addons de Scripting Eclipse (EASE) Não São Pip-Instaláveis

Quando a documentação de um projeto Eclipse/RCP anuncia "API Python" ou
libs como `python4capella`, `pydev` etc., é fácil presumir que dá pra
`pip install` e importar do processo Python externo. Isso está errado.
Ferramentas construídas sobre **Eclipse EASE** rodam o interpretador
Python *dentro* do processo Java/Eclipse (via bridge **Py4J**), não como
módulo standalone.

**Sintoma**: procurar no PyPI e não achar nada, ou achar um pacote de nome
parecido que não faz o que a doc descreve; exemplos de código usam
`include('workspace://...')` em vez de `import`.

**Fix / como confirmar antes de assumir**: checar se a lib depende de
"Eclipse", "EASE", "PyDev" ou "Py4J" na doc de instalação — se sim, a
única forma de acionar programaticamente de fora do Eclipse é via CLI
headless do produto (`<produto>c -application ... -appid ...`),
tipicamente exigindo GUI/window manager mesmo headless (Xvfb no Linux).
Tratar como integração via subprocess/processo externo, nunca como
dependência de biblioteca importável.

Caso concreto: `python4capella` (labs4capella/python4capella).

## 🔗 Conexões
- [[Capella MBSE]]
