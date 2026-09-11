---
title: Notas de Análise Envelhecem em Dias — Reverificar no Código Antes de Apresentar
type: trap
tags: [agentic-ai, documentation, git, dev-workflow, presentation, verification]
created: 2026-09-11
provenance: projetos_ita
project: projetos_ita
verified: 2026-09-11 via git log em capella_mcp e capella_llm_window
---

# Notas de Análise Envelhecem em Dias — Reverificar no Código Antes de Apresentar

## Contexto

Montando três apresentações sobre o estado do `capella_mcp` + `capella_llm_window`,
o agente usou como fonte de verdade os documentos de análise em `notes/analysis/`,
escritos em 04/09/2026. Eles diziam: P8 (`remove_from_diagram`) e P9 pendentes,
e P3/P4/P5/P10 "prontos mas aguardando release" — o PR `develop`→`master` nunca
aberto.

Os decks foram construídos e publicados em cima disso. Só depois, conferindo por
outro motivo (a contagem de tools), o agente rodou `git log` nos dois repositórios
e descobriu que **tudo tinha mudado em seis dias**:

- `capella_llm_window`: PR #20 mergeado e **tag `v0.0.5` publicada** — P3/P4/P5/P10
  estavam em produção, não "pendentes".
- `capella_mcp`: commits `07a57da` ("feat: add remove_from_diagram tool (P8)") e
  `7eb51e8` (P9), com testes de integração reais.

O placar apresentado era "8 de 11 propostas resolvidas". O real era **10 de 11**.
Os três decks tiveram que ser corrigidos e republicados.

## Armadilha

Documento de análise é um **retrato datado**, não um estado. Num projeto em
desenvolvimento ativo, a meia-vida dele é de dias — às vezes menos. O agente tratou
o documento como autoridade porque ele era detalhado, bem escrito e recente o
bastante para "parecer" atual. Detalhe e boa redação não são sinais de atualidade.

Pior: o erro era na direção que **subestima** o trabalho feito. Apresentar ao
orientador um placar pior que o real é um custo concreto, não só uma imprecisão.

## Quando aplicar

Antes de publicar, apresentar ou tomar decisão em cima de qualquer afirmação de
estado ("X está pendente", "Y não foi lançado", "falta implementar Z") que veio de
um documento e não do código:

- `git log --oneline -N` nos repositórios envolvidos
- `git tag` para claims sobre release
- `grep`/`ls` para claims sobre existência de arquivo, função ou ferramenta

Vale citar a própria reverificação como sinal de método — na apresentação virou uma
linha honesta: "estado verificado no código em 10/09; as notas de 04/09 já estavam
defasadas".

Regra prática: **quanto mais ativo o desenvolvimento, menor a validade da nota**.
Um repositório com 40 commits em oito dias invalida documentação de status quase na
mesma velocidade em que a produz.

## 🔗 Conexões
- [[Confirmar Qual Worktree Está Sendo Testada Antes de Diagnosticar]]
- [[Tag de Release Não Volta Pra Develop Sozinha]]
- [[Padrão de Documentação Agêntica Local]]
