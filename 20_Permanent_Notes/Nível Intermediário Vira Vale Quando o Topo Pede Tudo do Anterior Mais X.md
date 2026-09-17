---
title: Nível Intermediário Vira Vale Quando o Topo Pede Tudo do Anterior Mais X
type: pattern
tags: [rubric, grading, education, measurement, rubric-design]
created: 2026-09-17
provenance: correcoes_docs_tcc
project: correcoes_docs_tcc
verified: 2026-09-17 via distribuição das 16 notas em NOTAS.md
---

# Nível Intermediário Vira Vale Quando o Topo Pede Tudo do Anterior Mais X

Rubrica de cinco níveis aplicada a 16 entregas reais produziu esta distribuição:

| Nível | Nota | Grupos | n |
|---|---|---|---|
| 4 Avançado | 2.2 | 8 | 50% |
| 3 Adequado | 1.65 | 1 | 6% |
| 2 Básico | 1.1 | 7 | 44% |
| 1 Insuficiente | 0.55 | 0 | — |
| 0 Ausente | 0 | 0 | — |

O nível 3 — que a rubrica descreve como o estado **normal** de um repositório correto — apareceu uma
única vez. Os níveis 0 e 1 nunca dispararam.

## O mecanismo

O gatilho do nível 4 era "tudo do nível 3 **mais** esquemáticos e diagramas excelentes, código
modular, manual sem ambiguidade". Esse "mais X" não é independente do nível 3: quem teve disciplina
para não deixar nada implícito no README quase sempre também desenhou o diagrama e modularizou. **O
X correlaciona com o piso**, então quem alcança o piso salta o degrau.

Do outro lado, o nível 2 tinha gatilho barato (*um* passo essencial omitido) e **dois caminhos de
entrada** — a regra geral e um teto específico ("projeto com hardware e sem esquemático: teto nível
2"). Duas portas largas embaixo, uma ponte curta em cima: o meio esvazia.

Resultado prático: a régua de cinco níveis operou como **porta binária** — *o repositório é
reproduzível por leitura, sim ou não*. Um único eixo dos cinco (o README passo a passo) decidiu 6
das 7 notas baixas. Os outros quatro eixos quase não discriminaram.

## A regra que fica

**Medir a distribuição depois do primeiro lote, antes de confiar na rubrica.** Nível do meio vazio
não é coincidência estatística de uma turma boa ou ruim: é sinal de que a fronteira real não está
onde a rubrica pensa que está. Três reações possíveis, nessa ordem:

1. Verificar se o nível de cima pede algo que já está implícito no de baixo — se pede, o degrau é
   fictício e a rubrica tem menos níveis do que anuncia.
2. Verificar quantos caminhos levam ao nível de baixo. Gatilho com duas portas atrai desproporcional.
3. Só então considerar mexer no critério — e, se mexer, sob a regra de que o gabarito muda **para a
   frente** e não renota o que já foi confirmado (ver [[Rubrica em Prosa Vira Gabarito de Evidência]]).

Corolário para quem projeta rubrica: níveis que nunca disparam em um lote inteiro (aqui, 0 e 1) não
são inofensivos. Eles dão à rubrica uma aparência de granularidade que a aplicação não tem, e
escondem que a decisão real é binária.

## 🔗 Conexões
- [[Rubrica em Prosa Vira Gabarito de Evidência]]
- [[Validação Acadêmica Automatizada]]
- [[correcoes_docs_tcc]]
