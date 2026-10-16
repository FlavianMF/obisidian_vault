---
title: PRDs em Sequência - Implementar Cada PRD Antes de Escrever o Próximo
type: decision
tags: [prd, planejamento, workflow, mvp, project-methodology]
created: 2026-10-16
provenance: outlet_promo
project: outlet_promo
seen_in: [outlet_promo]
verified: 2026-10-16 via discussão de decisão no outlet_promo (ainda sem PRD 2 implementado)
confidence: low
scope: global
---

# PRDs em Sequência - Implementar Cada PRD Antes de Escrever o Próximo

## Decisão

Ao dividir um MVP em vários PRDs, escreva **um PRD, implemente, e só então detalhe o
próximo**. Não escreva todos os PRDs antes de começar a implementação.

Mantenha apenas um **mapa leve** do MVP: lista de features por PRD e dependências entre eles.
O PRD completo de cada etapa nasce quando a etapa anterior já está no código.

## Por quê

- A implementação revela premissas erradas, limites técnicos e erros de modelo de dados. PRDs
  escritos antes ficam obsoletos e geram retrabalho em cascata (documento e código).
- O primeiro PRD costuma ser a fundação (auth, schema, estrutura). Se ele muda, todos os
  seguintes mudam junto.
- Um PRD escrito com o código real como referência produz um plano melhor do que um PRD
  abstrato.

## Como aplicar

1. Faça o mapa geral de features (MVP v1 e backlog v2) antes de tudo.
2. Escreva o PRD N completo, implemente, teste e faça merge.
3. Antes do PRD N+1, releia o rascunho contra o código real e ajuste.
4. Repita.

PRDs já rascunhados antes da implementação anterior valem como **rascunho**, não como
contrato: releia antes de começar.

## Exceção

Escrever todos os PRDs antes só compensa para validar escopo, prazo ou orçamento globais, e
nesse caso o mapa leve normalmente basta.

## O que NÃO funcionou

Nada foi tentado e falhou ainda: a decisão vem de raciocínio, não de um projeto que escreveu
todos os PRDs antes e pagou o custo. Por isso `confidence: low` até um projeto confirmar.

## Relacionadas

- [[PRD]]
- [[Plano de Fase em Etapas Mescláveis]]
- [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]]
