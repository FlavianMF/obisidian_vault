---
title: PRD-004 — Golden Set Ampliado, Split Test e Rerank
type: project
tags: [prd, second-brain, rag, agentic-rag, retrieval, evaluation, golden-set]
created: 2026-10-23
provenance: obsidian_vault
project: second_brain_memory
confidence: low
verified: 2026-10-23 via contagem do golden.jsonl por split e do shadow.jsonl
scope: project
---

# PRD-004 — Golden Set Ampliado, Split Test e Rerank

**Status**: DRAFT em 2026-10-23 · Origem: [[PRD-003 - Agentic RAG no Second Brain]] (Resultado) · Estudo: [[Estudo - Agentic RAG no Second Brain]] (A4, A5) · Medições: [[F0 - Linha de Base de Tokens e Golden Set MVP]].

## Problem Statement

A A3 cumpriu success@5 e FP no limiar 0,35, mas falhou no piso de tokens por acerto, e os IC95 se sobrepõem. O golden set é pequeno demais para decidir o papel do L1. O `test` tem 10 queries, com 8 positivas, então ele mede em degraus de 0,125 e só pode rodar uma vez.

## Evidence

- O `golden.jsonl` tem 42 queries: `dev` com 19 positivas e 13 negativas, `test` com 8 positivas e 2 negativas (contagem de 2026-10-23).
- O success@5 = 0,84 do `rewrite` vale 16/19. O FP = 0,15 vale 2/13. O n efetivo é menor que 32.
- O `shadow.jsonl` tem 18 linhas. Ele cobre no máximo um terço do crescimento, então os rascunhos de LLM são a fonte principal.
- A reescrita nunca perdeu um acerto do `rank` e recuperou `q019` e `q026` ([[F0 - Linha de Base de Tokens e Golden Set MVP]], 2026-10-22).

## Proposed Solution

Três etapas em sequência, decididas pelo usuário em 2026-10-23:

1. **B1**: crescer o golden set para ≥ 60 queries e registrar a nova linha de base no `dev`.
2. **B2**: gerar as reformulações do `test` e rodar o `test` uma vez, no limiar 0,35.
3. **B3**: adaptador `rerank`, com julgamento do top-20 por Haiku sobre `title` e `summary` (CRAG-lite), medido no `dev`.

Alternativa descartada: rodar o `test` antes de crescer. Ela queimaria a única rodada com n = 8 positivas.

## Key Hypothesis

We believe que um golden set com ≥ 60 queries e um `test` com ≥ 24 queries will dar IC95 estreitos o bastante para decidir o L1 for o usuário que decide a A5.
We'll know we're right when o `rewrite` cumprir os pisos da A3 no `test`, ou falhar neles com veredito registrado, e o `rerank` tiver veredito no `dev`.

## What We're NOT Building

- Ativação ou aposentadoria do L1: a decisão (A5) vem depois desta fase, com os números dela.
- Mudança no `SKILL.md` ou no `Agent-Instruction.md`.
- LLM em tempo de hook ou de `sb search`.
- Embeddings, FTS5 ou índice novo.
- Métrica de adesão ao protocolo da A2 (B4): fica para uma fase futura.

## Success Metrics

Pisos escritos **antes** de qualquer medição e aprovados pelo usuário em 2026-10-23. Nenhum piso será afrouxado depois de medir.

### B1 — Golden set

| # | Metric | Target | How Measured |
|---|--------|--------|--------------|
| 1 | Total de queries | ≥ 60, com ≥ 18 novas | validador |
| 2 | Composição do `test` | ≥ 24 queries, com ≥ 16 positivas e ≥ 8 negativas | validador |
| 3 | Negativas no total | ≥ 30% | validador |
| 4 | Divisão `dev`/`test` | Fixa antes de rodar qualquer adaptador, por semente, sem olhar resultado | commit da divisão antes do commit da medição |
| 5 | Integridade | 0 paths esperados inexistentes e 0 duplicatas, exatas ou normalizadas | validador |
| 6 | Proveniência | Toda query nova tem `source` em `shadow`, `llm` ou `manual`. Toda query `llm` tem a aprovação do usuário registrada | validador |
| 7 | Rótulo cego | Os paths esperados são escritos sem ver a saída do `rank` | brief e prompt dos rascunhos |
| 8 | Nova linha de base | `rank` e `rewrite` no `dev` ampliado, registrados na F0. As reformulações das queries novas do `dev` entram no mesmo lote | `run_eval.py --methods rank,rewrite --split dev --k 5` |
| 9 | Pisos da A3 | Inalterados: success@5 ≥ 0,80, FP ≤ 0,20, tokens por acerto ≤ `rank`, no mesmo limiar | mesma execução |

### B2 — Split `test`

| Metric | Target | How Measured |
|--------|--------|--------------|
| success@5 do `rewrite` | ≥ 0,80 | `run_eval.py --methods rank,rewrite --split test --k 5 --min-coverage 0.35`, uma execução |
| FP do `rewrite` | ≤ 0,20 | mesma execução |
| Tokens por acerto | ≤ o do `rank` | mesma execução |

O limiar 0,35 fica fixo. Uma segunda execução no `test` não é permitida.

### B3 — Rerank

| # | Metric | Target | How Measured |
|---|--------|--------|--------------|
| 1 | success@5 e FP do `rerank` | ≥ 0,80 e ≤ 0,20 no mesmo limiar | `run_eval.py --methods rank,rerank --split dev --k 5` |
| 2 | Tokens por acerto | ≤ o do `rank` no mesmo limiar, só com o contexto que o agente recebe | mesma execução |
| 3 | Custo do juiz | Coluna separada, teto de 3000 tokens de entrada por query | mesma execução |
| 4 | Sem vazamento | O prompt do juiz leva só a query, o `title` e o `summary` dos 20 candidatos | teste do prompt montado |
| 5 | Escopo | Só no `dev`. Uma rodada no `test` exige nova aprovação do usuário | brief |

Um veredito negativo também é entrega. O critério é registrar o veredito contra os pisos na F0.

## Open Questions

- [ ] B1: como redigir positivas a partir de uma nota sem copiar o vocabulário do título? O planejador da B1 decide e justifica.
- [ ] B1: quais linhas do `shadow.jsonl` viram query? Só o `prompt` é usado. Os `candidates` mostram a saída do ranqueador e violam o piso 7.
- [ ] B1: as queries novas vão primeiro para o `test` até cumprir o piso 2? A divisão por semente precisa respeitar as cotas por split.
- [ ] B3: o juiz devolve uma lista ordenada ou um rótulo binário por candidato? O planejador da B3 decide.

---

## Users & Context

**Primary User**
- **Who**: o usuário, que decide o papel do L1 (A5) e paga os tokens.
- **Current behavior**: tem um veredito da A3 com n pequeno e IC95 sobrepostos.
- **Trigger**: decidir se o L1 sai da sombra, injeta uma linha só, ou é aposentado.
- **Success state**: os números do `test` e do `rerank` sustentam uma decisão escrita.

**Job to Be Done**
When o usuário vai decidir o papel do L1, I want to ter números com IC95 úteis, so I can não decidir por ruído.

**Non-Users**
O agente em sessão normal: nada muda no comportamento dele nesta fase.

---

## Solution Detail

### Core Capabilities (MoSCoW)

| Priority | Capability | Rationale |
|----------|------------|-----------|
| Must | Validador do golden set com os pisos 1 a 6 da B1 | Pisos verificados por código, não por leitura |
| Must | Campo `source` e registro de aprovação nas queries novas | Proveniência auditável |
| Must | Reformulações do `test` e das queries novas do `dev` | Pré-requisito da B1 (piso 8) e da B2 |
| Must | Adaptador `rerank` com julgamentos em cache | Testa a A4 sem LLM por execução |
| Should | Gerador de rascunhos de query com aprovação em lote | Reduz o tempo do usuário |
| Won't | Métrica de adesão (B4), mudança no L1 | Ver "What We're NOT Building" |

### MVP Scope

B1, B2 e B3. O MVP está completo quando a F0 tiver três seções datadas, uma por etapa, cada uma com veredito.

---

## Technical Approach

**Feasibility**: HIGH. Python stdlib sobre `00_META/eval/`, com o mesmo isolamento de `claude -p` do `gen_rewrites.py`.

**Architecture Notes**
- O `golden.jsonl` e o `rewrites.jsonl` ficam em `00_META/eval/`. O `gen_rewrites.py` é idempotente e só gera linhas que faltam.
- O `RewriteAdapter` do `run_eval.py` é o molde do `RerankAdapter`.
- Os julgamentos do juiz ficam num arquivo próprio, gerados uma vez, com `model` e `created`, como o `rewrites.jsonl`.
- Toda chamada paga em lote passa por `--dry-run` e depois `--limit 1` antes do resto.

**Technical Risks**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Rascunhos de LLM copiam o vocabulário da nota e inflam o success@5 | H | Prompt proíbe palavras do título; o usuário aprova cada query |
| Rótulo influenciado pela saída do `rank` | M | Piso 7; os `candidates` do shadow ficam fora |
| Divisão escolhida depois de ver resultado | L | Commit da divisão antes do commit da medição |
| Vazamento do gabarito no prompt do juiz | M | Piso 4 da B3, com teste |
| Linha de base do `rank` muda com o vault | H | Comparar sempre com o `rank` da mesma execução |

---

## Implementation Phases

| # | Phase | Description | Status | Parallel | Depends | PRP Plan |
|---|-------|-------------|--------|----------|---------|----------|
| 1 | B1 — Golden set ≥ 60 | Validador, rascunhos, aprovação, divisão, reformulações novas, linha de base `dev` | pending | - | - | `~/obsidian_vault/.claude/PRPs/plans/b1-golden-set.plan.md` |
| 2 | B2 — Split `test` | Uma execução no `test`, limiar 0,35 | pending | - | 1 | `~/obsidian_vault/.claude/PRPs/plans/b2-split-test.plan.md` |
| 3 | B3 — Rerank | `RerankAdapter`, julgamentos em cache, medição no `dev` | pending | - | 1 | `~/obsidian_vault/.claude/PRPs/plans/b3-rerank.plan.md` |

### Phase Details

**Phase 1: B1 — Golden set ≥ 60**
- **Goal**: dar ao eval um n que separe os métodos.
- **Scope**: validador; campo `source`; rascunhos de query a partir do `prompt` do shadow e de notas do vault; aprovação do usuário; divisão por semente; reformulações das queries novas; nova linha de base no `dev`.
- **Success signal**: pisos 1 a 8 da B1 cumpridos e a seção datada na F0.

**Phase 2: B2 — Split `test`**
- **Goal**: medir o `rewrite` fora do split onde o limiar foi escolhido.
- **Scope**: `gen_rewrites.py` nas queries do `test`; uma execução; seção datada na F0.
- **Success signal**: veredito contra os pisos da B2. A rodada exige aprovação explícita do usuário na hora.

**Phase 3: B3 — Rerank**
- **Goal**: testar se o julgamento por LLM corta falsos positivos sem perder acertos.
- **Scope**: gerador de julgamentos idempotente com `--dry-run` e `--limit`; `RerankAdapter`; testes sem rede; medição no `dev`; seção datada na F0.
- **Success signal**: veredito contra os pisos da B3.

### Parallelism Notes

A B2 e a B3 dependem só da B1. Por decisão do usuário, rodam em sequência: B1, B2, B3.

---

## Execução por agentes

**Hierarquia.** O coordenador (Opus) decide escopo e pisos, revisa plano e diff, faz merge e escreve no vault. Um planejador Opus novo por etapa escreve o plano `/prp-plan`. Um implementador Sonnet por plano escreve testes primeiro, código e um commit. Um executor Haiku faz tarefa mecânica com entrada e saída fechadas.

**Teste de aninhamento (2026-10-23): funcionou.** Um agente Sonnet abriu um agente Haiku pela ferramenta Agent e devolveu `ok`. Os implementadores abrem executores Haiku direto. O caminho por `claude -p` fica só para chamadas em lote do eval, como no `gen_rewrites.py`.

**Ambiente.** Um worktree por etapa: `~/obsidian_vault-wt/<etapa>` na branch `feat/<etapa>`, criada a partir do `master`. O checkout principal fica no `master`, para o `sb sync` funcionar. Os planos ficam em `~/obsidian_vault/.claude/PRPs/plans/`, no checkout principal, porque a remoção do worktree apagou os planos do PRD-003.

**Portões do coordenador:**

- Conferir no código 2 ou 3 afirmações centrais do plano antes de liberar o implementador.
- Rodar os testes do escopo no diff. Se `test_prompt_hint.RealVaultSmokeTest` falhar, repetir antes de culpar a mudança.
- Antes de chamada paga em lote, conferir `--dry-run` e `--limit 1`.
- Na B1, mostrar os rascunhos ao usuário antes de gravar no `golden.jsonl`.
- Na B2, pedir aprovação explícita antes de rodar o `test`.

---

## Decisions Log

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Ordem | B1, B2, B3 em etapas separadas | B2 primeiro; B3 antes de B1 | Não queimar o `test` com n = 8 positivas (usuário, 2026-10-23) |
| Pisos da B1 | Itens 1 a 9 | Só contagem total | Aprovados pelo usuário em 2026-10-23 |
| Pisos da B2 | Os três da A3, limiar 0,35, uma execução | Novo limiar no `test` | Aprovados pelo usuário em 2026-10-23 |
| Pisos da B3 | Itens 1 a 5 | Ganho relativo sobre o `rewrite` | Aprovados pelo usuário em 2026-10-23 |
| B4 | Fora desta fase | Junto com B1 | A métrica ainda não existe; não bloqueia o L1 |
| Aninhamento | Sonnet abre Haiku pela ferramenta Agent | `claude -p` por Bash | Teste de 2026-10-23 funcionou |

---

*Generated: 2026-10-23*
*Status: DRAFT - pisos aprovados, nenhuma medição feita*
