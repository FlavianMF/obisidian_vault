---
title: Migrar Vários Documentos para um Design System Preservando Nomes de Token e Classe
type: pattern
tags: [css, refactoring, design-system, html, agentic-ai]
created: 2026-09-11
provenance: projetos_ita
project: projetos_ita
---

# Migrar Vários Documentos para um Design System Preservando Nomes de Token e Classe

## Contexto

Três decks HTML tinham sido escritos em momentos diferentes, com identidades visuais
distintas. O pedido: "atualize as demais apresentações para seguir o mesmo padrão
visual" do terceiro.

A abordagem óbvia — copiar o CSS do deck novo e renomear as classes nos outros dois —
implicaria mexer em centenas de linhas de markup e dentro dos SVGs inline (que
referenciam tokens em `fill="var(--ink)"`, `stroke="var(--line-strong)"`). Muito
trabalho manual, muita chance de quebrar um `<text>` de gráfico sem perceber.

## Padrão

Antes de migrar, **inventariar os nomes usados** nos documentos-alvo:

```bash
grep -o '\-\-[a-z0-9-]*:' arquivo.html | sort -u          # tokens
grep -o 'class="[a-z0-9 -]*"' arquivo.html | sed 's/class="//;s/"//' \
  | tr ' ' '\n' | sort -u                                  # classes
```

Os dois decks usavam **exatamente o mesmo vocabulário** entre si (`--paper`, `--ink`,
`--ink-muted`, `--line-strong`, `.slide-title`, `.statrow`, `.badge`, `.tl-col`…).
Isso mudou a estratégia: em vez de adaptar o markup ao CSS novo, escrever **um CSS
novo que responde pelos nomes antigos** — mesma semântica, valores novos.

```
--paper:  #eef0f2 (cinza-frio)  →  #faf9f7 (papel quente)
--accent: #c15f0a (âmbar)       →  #b3593b (terracota)
--accent-2: #0f7c82 (teal)      →  #cc785c (terracota clara)
```

O resultado: uma folha de estilo escrita uma vez, injetada nos dois arquivos com um
`re.sub(r"<style>.*?</style>", ...)`, **zero mudança de markup e zero mudança nos
SVGs**. O que era um refactor de risco virou uma substituição de bloco.

Onde o vocabulário novo não existia (uma classe `.shot` para screenshots), bastou
acrescentar — adicionar é seguro, renomear é que não é.

## Quando aplicar

Qualquer unificação visual de N documentos/páginas independentes. O passo que decide
a estratégia é o inventário: se os alvos compartilham vocabulário, preserve-o e troque
só valores; se divergem, aí sim vale normalizar os nomes primeiro — mas sabendo que
esse é o caminho caro.

Vale também para migração de tema em app: manter o nome do token e trocar o valor é
quase sempre mais barato que renomear token em todo o código.

## 🔗 Conexões
- [[Substituir Imagem por Placeholder no Template e Injetar Data URI no Build]]
- [[Página com Screenshots de Um Tema Não Deve Suportar o Tema Oposto]]
