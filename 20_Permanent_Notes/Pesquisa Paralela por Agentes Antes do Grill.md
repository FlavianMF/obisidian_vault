---
title: Pesquisa Paralela por Agentes Antes do Grill
type: pattern
tags: [grilling, subagents, research, agentic-ai, project-methodology, decision-making]
created: 2026-10-05
provenance: residencia_cariri_projects
seen_in: [residencia_cariri_projects]
verified: 2026-10-05 via sessão de migração Trello→JIRA (4 agentes + 2 rodadas de grill)
confidence: low
---

# Pesquisa paralela por agentes antes do grill

## O padrão

Para decidir uma metodologia ou um desenho com o usuário, dispare **em paralelo** agentes
de fatos, um por eixo:
- domínio externo A (ex.: a ferramenta);
- domínio externo B (ex.: o framework de processo);
- estado atual do repositório;
- insumos novos (ex.: as prioridades recém-definidas).

Enquanto eles rodam, abra o grill só com as decisões que **não dependem** dos fatos
pendentes. Cada pergunta leva uma resposta recomendada. Quando cada agente volta,
**revise as recomendações** em voz alta antes de abrir a rodada seguinte.

## Por que funciona

Os fatos mudaram as recomendações. No caso real, três dos quatro agentes inverteram uma
sugestão inicial:
- O agente da ferramenta mostrou que o plano Free limita a 10 usuários (a turma tinha
  34).
- O agente do repositório mostrou que nada havia sido alocado e que os boards nunca foram
  criados. A pergunta "como migrar" virou "começar do zero".
- Os agentes de domínio divergiram sobre o que é um épico (o projeto inteiro ou o grupo de
  entregas). Isso virou uma pergunta explícita ao usuário, em vez de uma suposição.

O usuário respondeu em lote (Q1–Q8, depois Q9–Q18). Duas rodadas bastaram para fechar
cerca de 18 decisões.

## Cuidados

- O agente de fatos **não decide**. Divergência entre agentes vira pergunta, com as
  opções lado a lado.
- O usuário pode ter um fato que nenhum agente acha (aqui, "temos JIRA Enterprise").
  Pergunte cedo sobre o ambiente e o plano.
- Agentes de pesquisa web citam fontes de memória. Peça para marcar o que não foi aberto
  na sessão.
- Depois do grill, delegue a geração de artefatos independentes (um backlog por agente)
  e mantenha na sessão principal o que cruza tudo (gerador, documentação).

Relacionado: [[Pedido de Sistema Novo Costuma Ser Delta de Sistema Existente]],
[[Scrum Enxuto para Residência com Alunos em Tempo Parcial]].
