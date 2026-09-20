---
title: Design de Interface com Agente
type: moc
tags: [moc, design, frontend, agentic-ai, ux, claude-code]
created: 2026-09-20
provenance: impeccable
---

# 🎨 Design de Interface com Agente (MOC)

Mapa do que o vault sabe sobre **fazer um agente produzir interface que se assine**: por que
o default sai igual em todo projeto, o que decidir antes do código, o que dá para checar por
máquina, e quando parar.

Nasceu da instalação e da leitura da skill [[Impeccable]] (v4.3.1, set/2026), cruzada com as
notas de craft de frontend que já estavam aqui.

## 🧭 Comece por aqui

- [[Slop de IA é Convergência de Treino, Não Falta de Gosto]] — o catálogo dos tells e o
  autoteste: se dá pra adivinhar a estética só pela categoria, refaz.
- [[Contrato de Direção Antes do Código]] — os seis blocos que transformam "clean e moderno"
  em decisão auditável, com a condição de saída escrita junto.
- [[Modo do Visitante Escolhe o Conjunto de Regras]] — Persuade, Operate, Read, Experience;
  escolhido pela superfície, nunca pelo produto.

## 🛠️ Instrumental

- [[Impeccable]] — a ferramenta: 23 comandos, 4 subagentes, binário de detecção, `PRODUCT.md`
  e `DESIGN.md`. Inclui a armadilha de instalação com `sudo` que custa uma hora.
- [[Detector Determinístico Fora do LLM como Piso de Qualidade]] — o subconjunto mecânico sai
  do prompt e vira exit code; o LLM fica com o julgamento.
- [[Verificação em Passes Limitados, Não em Loop]] — teto declarado para auto-QA, e o backlog
  persistido que torna parar seguro.
- [[Uma Fonte de Regra, N Harnesses Compilados]] — prompt como artefato compilado, com patch
  de viés por modelo e manifest de hook por harness.

## ⚠️ Armadilhas

- [[Design System Documentado Depois do Build, Não Antes]] — rulebook escrito cedo vira coisa
  a defender, e alvo instável pro detector.
- [[Página com Screenshots de Um Tema Não Deve Suportar o Tema Oposto]] — o tema que a página
  promete tem que ser o tema das imagens dentro dela.
- [[Campo de Settings Só Deve Ser Editável Se Aplicar de Verdade]] — controle que não aplica
  é mentira de interface, não afordância.

## 🧱 Craft de frontend já no vault

- [[Deck HTML Precisa Escalonar por Altura de Viewport, Não Só por Largura]] — responsivo não
  é só largura quando o conteúdo tem que caber inteiro na tela.
- [[Migrar Vários Documentos para um Design System Preservando Nomes de Token e Classe]] — como
  trocar o sistema visual sem quebrar o que já referencia os nomes.
- [[Reproduzir a UI com o CSS Real do Produto Quando Não Há Screenshot]] — a fonte de verdade
  visual é o CSS do produto, não a lembrança dele.
- [[Substituir Imagem por Placeholder no Template e Injetar Data URI no Build]] — separar o
  template do peso do asset.
- [[Screenshot de UI Comprime Melhor com Quantização de Cores que com JPEG]] — captura de
  interface é imagem de poucas cores, não fotografia.
- [[Anatomia de uma Landing de Agente - Posicionar Ferramenta de Pesquisa como Produto]] — um
  caso concreto de superfície Persuade.

## 🔗 Relacionado

- [[Tecnologias Web]] — stack por baixo da interface.
- [[claude-code]] e [[opencode]] — os harnesses onde a skill roda.
- [[Rubrica em Prosa Vira Gabarito de Evidência]] — a mesma ideia do detector, aplicada a
  texto acadêmico.
