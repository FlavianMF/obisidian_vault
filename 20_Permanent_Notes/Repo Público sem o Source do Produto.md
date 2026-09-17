---
title: Repo Público sem o Source do Produto
type: trap
tags: [research-method, oss, licensing, reverse-engineering, documentation]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

# Repo Público sem o Source do Produto

**Armadilha:** um repositório público com 145 mil estrelas, README, CHANGELOG e código dentro
parece o código-fonte do produto. Muitas vezes não é — e pesquisar como se fosse leva a
conclusões erradas ou a atravessar um limite legal sem perceber.

Caso concreto, `anthropics/claude-code` (2026-09): 1153 arquivos, 31 MB, `LICENSE.md` com uma
linha — *"© Anthropic PBC. All rights reserved"*. O produto é um binário compilado de ~230 MB
que **não está lá**. O que está: a superfície de extensão, exemplos de política, artefatos de
deploy, e o histórico.

## Como não cair

1. **Ler `LICENSE` antes de qualquer outra coisa.** Ausência de licença OSS não é descuido: é
   a informação principal sobre o que se pode fazer com o que se ler.
2. **Comparar ordens de grandeza.** Repo de 31 MB versus binário de 230 MB responde sozinho se
   o source está ali.
3. **Não desmontar o binário.** `strings`, descompilação e desmontagem de produto proprietário
   são reverse engineering, geralmente vedado pelos termos comerciais — e desnecessário, na
   maior parte dos casos, para o que se quer saber.

## O que fazer em vez disso

A superfície legítima costuma ser mais rica do que a primeira impressão sugere. Neste caso:

| Fonte | O que entrega |
|---|---|
| Declarações de tipo publicadas | O contrato inteiro da arquitetura de extensão ([[Contrato de API que Documenta Comportamento e Custo]]) |
| Plugins/mods built-in com source | Como o próprio fabricante escreve contra a própria API |
| CHANGELOG longo | Onde o sistema quebra na prática, por peso de tema |
| CI do próprio repo | Como o fabricante roda o produto sem supervisão |
| Artefatos em disco da instalação local | Formatos de persistência, sem tocar no binário |

A última linha é a distinção que vale reter: **observar o que um programa escreve em disco não
é engenharia reversa**. Layout de diretório, esquema de JSONL, chaves de configuração são
dados do próprio usuário, e frequentemente respondem melhor que qualquer desmontagem
responderia.

## Regra prática

Declarar o limite **no próprio documento de pesquisa**, junto com o que foi usado. Um leitor
(ou um orientador, ou você mesmo daqui a um ano) precisa saber que nenhuma afirmação depende
de fonte proibida. Ver `40_Projects/claude_code/21_fontes.md` para o formato usado.

Relacionado: [[claude-code]], [[opencode]] (contraste — MIT, source completo, e por isso o
estudo daquele lado pôde ser de implementação, não só de contrato).
