---
title: Pedido de Sistema Novo Costuma Ser Delta de Sistema Existente
type: pattern
tags: [requirements, scope, agentic-ai, project-methodology, grilling, dev-workflow]
created: 2026-09-20
provenance: orbita-platform
project: orbita-platform
---

# Pedido de Sistema Novo Costuma Ser Delta de Sistema Existente

## O padrão

Quando o usuário pede "um sistema novo" descrevendo funcionalidades, a
descrição costuma ser de **capacidades**, não de código inexistente. Num
projeto maduro, boa parte já está construída — muitas vezes sob outro nome.

Caso real: o pedido foi "uma plataforma para listar empresas em que os
clientes da consultoria têm desconto; o admin cadastra as empresas; o cliente
se cadastra, faz login e acessa o link". Dos quatro itens, **três já existiam
e estavam em produção**, sob o nome "vitrine de parceiros", entregues seis
etapas antes. O delta real era desconto, tenant e gate de vínculo.

Planejar sem descobrir isso teria produzido tabela duplicada, segundo CRUD,
segunda tela e duas verdades sobre a mesma empresa.

## Como aplicar

**Antes de planejar, faça a busca de existência — e faça você, não o usuário.**
Duas varreduras baratas resolvem:

1. **Pelo vocabulário do usuário e pelos sinônimos do domínio.** O usuário
   disse "empresas parceiras com desconto"; o código dizia `Parceiro`. Grep
   por *ambos* os vocabulários, e pelos termos que o delta exigiria
   (`desconto|cupom|voucher|cashback`) — a ausência deles é o que delimita o
   que realmente falta.
2. **Nos documentos de decisão, não só no código.** Um RFC costuma dizer
   explicitamente o que ficou **fora** de escopo e por quê ("sem segmentação,
   tracking de cliques ou comissionamento — isso é a Fase 3"). Isso é ouro
   duas vezes: mostra que a decisão foi deliberada, e diz qual decisão
   precisa ser **emendada** se o novo pedido a contradiz.

**Depois, apresente o achado antes das perguntas.** Abrir a curadoria com
"90% disso já existe, aqui está onde; o delta é X" muda as perguntas que valem
a pena fazer. A primeira pergunta deixa de ser "como construir" e vira
"estender o que existe ou construir separado" — que é a decisão de arquitetura
de verdade, e é do usuário.

**Espere uma contradição e a levante.** No caso real, o usuário escolheu
"produto separado, multi-tenant, vendável a terceiros" e, na mesma rodada,
"só cliente com vínculo ativo na tabela X" — que é tabela deste produto. As
duas respostas só coexistem se "separado" significar subdomínio e marca, não
base de dados própria. Apontar a incompatibilidade na rodada seguinte, com
opções concretas, resolveu em uma pergunta o que teria custado uma fase.

## Por que isso não é só "pesquisar antes"

A diferença é **onde** o custo cai. Descobrir depois de planejar significa
jogar fora o plano; depois de implementar, significa migração de dados e duas
verdades no banco. E o usuário raramente tem como saber: ele pede pelo
resultado, não pelo nome interno da tabela — achar a sobreposição é trabalho
de quem lê o código.

Relacionado: [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]],
[[Playbook de Projeto - Erros Já Cometidos Como Artefato]],
[[Notas de Análise Envelhecem em Dias - Reverificar no Código Antes de Apresentar]].
