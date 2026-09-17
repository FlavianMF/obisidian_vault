---
title: Rubrica em Prosa Vira Gabarito de Evidência
type: pattern
tags: [education, grading, rubric, agentic-ai, documentation, reproducibility]
created: 2026-09-17
provenance: correcoes_docs_tcc
project: correcoes_docs_tcc
---

# Rubrica em Prosa Vira Gabarito de Evidência

Rubrica acadêmica é escrita em adjetivos — "documentação primorosa", "código pouco legível",
"repositório organizado". Adjetivo não se aplica duas vezes do mesmo jeito: o mesmo repositório
recebe notas diferentes dependendo do dia e da ordem de leitura. O passo que falta entre a rubrica e
a correção é um **gabarito**: um documento intermediário que traduz cada nível em evidência
localizável no repositório.

Destilado de `correcoes_docs_tcc` (correção conversacional, um repo por vez), irmão menor de
[[Validação Acadêmica Automatizada]] (pipeline em massa do [[hermes_validator]]). O que se replica
entre os dois não é a infraestrutura — é a rubrica-como-artefato e o gate humano.

## As quatro regras que fazem o gabarito funcionar

**1. Eixos de evidência vêm do enunciado, não da rubrica.** A rubrica diz o nível; o enunciado diz
o que tinha que ser entregue. Cada artefato obrigatório vira um eixo (`E1..En`) com uma coluna
"como verificar no clone". A rubrica sozinha não é verificável; o enunciado sozinho não é graduado.

**2. O nível é o menor que a evidência sustenta.** Eixo excelente não compensa eixo ausente. Sem
essa regra escrita, a média informal sobe a nota de toda entrega mediana com um detalhe brilhante.

**3. Evidência localizada ou nada.** Toda linha da avaliação cita `arquivo:linha`; toda ausência
cita a busca que a provou ("nenhum `.fzz`, `.sch`, `.kicad_sch` ou imagem de circuito na árvore").
Afirmação sem localização não sobrevive a uma contestação do aluno — e o agente é bom demais em
produzir prosa plausível sem lastro.

**4. "Se aplicável" precisa ser explícito, senão vira desconto fantasma.** Enunciado que pede
esquemático elétrico *se aplicável* exige uma regra escrita: projeto sem hardware registra `n/a`
com justificativa e **não** perde ponto. Sem isso o aluno é penalizado por não entregar o que não
lhe foi pedido, e ninguém percebe porque o desconto acontece por omissão.

## O gate humano tem uma forma específica

Não é "o professor revisa depois". É um campo de status no documento:

- A nota do agente nasce **`PROPOSTA`**.
- Vira **`CONFIRMADA`** quando o professor preenche o bloco de nota final.
- **A proposta nunca é apagada quando a nota manual diverge** — ficam as duas, lado a lado. A
  divergência é o dado mais útil do sistema: é ela que mostra onde o gabarito está errado.
- Reexecutar a correção sobre grupo já `CONFIRMADA` reporta conflito e não sobrescreve.

## O gabarito é versionado, e muda só para frente

O gabarito carrega número de versão. Mudou regra de decisão, subiu a versão — e avaliações já
confirmadas sob a versão anterior **não são renotadas**. Renotar retroativamente é reabrir nota
fechada com aluno; a divergência de critério fica registrada, não apagada. Mesmo espírito da catraca
de cobertura do [[Checklist de Bootstrap de Workflow de Desenvolvimento]]: o valor de hoje é o piso
de amanhã, e baixá-lo exige justificativa escrita.

Cada avaliação também registra o **commit avaliado** do repositório do aluno. Sem isso não há como
responder "esta nota olhou para qual estado do repo" — o aluno pode ter empurrado commits depois.

## 🔗 Conexões
- [[Validação Acadêmica Automatizada]] (o irmão em massa)
- [[hermes_validator]]
- [[Documentação Desatualizada é Bug, Não Dívida]]
- [[Checklist de Bootstrap de Workflow de Desenvolvimento]]
- [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]]
