---
title: Verificação em Passes Limitados, Não em Loop
type: pattern
tags: [agentic-ai, quality, verification, cost, claude-code, workflow]
created: 2026-09-20
provenance: impeccable
---

# Verificação em Passes Limitados, Não em Loop

**Auto-QA de agente precisa de teto declarado, não de condição de parada implícita.**
[[Impeccable]] põe isso entre os três princípios de topo do `SKILL.md`, com a justificativa
econômica explícita: *open-ended self-QA burns the user's money doing worse what the finish
handoffs do better.* O ciclo prescrito é fechado:

1. **Construir inteiro.** Nada de verificar pedaço por pedaço enquanto se constrói.
2. **Uma rodada de inspeção em lote** — desktop e mobile na mesma passada, ou todas as
   classes de dispositivo entregues, de uma vez.
3. **Corrigir tudo o que ela mostrou, num lote só.**
4. **No máximo mais uma rodada de confirmação.**
5. **Parar.**

O detalhe que fecha a brecha: **o teto cobre o ciclo inteiro**, não só os screenshots.
Scan de defeito, micro-edição e rebuild contam para o mesmo orçamento. Sem isso, o agente
respeita o limite de screenshots e reabre o loop por outra porta — "só mais um ajuste",
que dispara outro scan, que produz outro achado.

## Por que o loop aberto é pior, e não só mais caro

Um agente que revisa o próprio trabalho em loop sem teto converge para micro-otimização:
ele encontra sempre alguma coisa, porque o critério dele é "está perfeito?" e a resposta é
sempre não. O trabalho que o loop faz mal é justamente o que um passo especializado de
finish faz bem — um revisor separado, com o contrato de direção na mão, auditando o render
contra o que foi prometido. Loop é substituto ruim de handoff.

## Handoff com estado, não com memória

O mecanismo que permite parar é o achado ficar registrado fora da conversa. Em Impeccable,
`critique` persiste um snapshot com o score heurístico, a contagem de P0/P1 e um
fingerprint exato do conteúdo avaliado; `polish` depois **lê esse snapshot como backlog** e
o fecha quando resolve os itens ou quando o fingerprint mostra que ele ficou obsoleto. O
fingerprint é o que distingue "os bytes que eu avaliei" de "os bytes que existem agora",
sem depender de estado do git nem de timestamp.

Isso é o que torna o teto seguro: parar não perde informação, porque o que sobrou está
escrito. Mesma lógica de [[Hook Escreve Estado, Renderizador Lê Tudo Num Passe]].

## Generaliza

Qualquer agente com ciclo de auto-avaliação precisa dos dois: **um teto que cubra todas as
formas do ciclo** e **um lugar persistido onde o resíduo é anotado**. Vale para correção de
teste que falha, para revisão de código, para refinamento de texto. O critério verificável
em si é assunto de [[Matriz de V&V - Birthday Counter]]; a condição de saída escrita antes
é o bloco FINISH de [[Contrato de Direção Antes do Código]]; a parte mecânica que não
precisa de rodada nenhuma é
[[Detector Determinístico Fora do LLM como Piso de Qualidade]].
