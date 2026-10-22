---
title: PRD-003 — Agentic RAG no Second Brain
type: project
tags: [prd, second-brain, rag, agentic-rag, retrieval, evaluation]
created: 2026-10-22
provenance: obsidian_vault
project: second_brain_memory
confidence: low
verified: 2026-10-22 via leitura de sb.py, run_eval.py, vault_rank.sh e dos manifests
scope: project
---

# PRD-003 — Agentic RAG no Second Brain

**Status**: DRAFT, decisões fechadas em 2026-10-22 · Origem: [[Estudo - Agentic RAG no Second Brain]] · Conceito: [[Agentic RAG]] · Contexto: [[RFC-001 - Memória de Agentes sobre o Second Brain com Orçamento de Tokens]].

## Problem Statement

O agente (Claude Code) consulta o vault por um ranqueador lexical. O ranqueador erra quando a pergunta usa outro vocabulário que a nota, e o hook L1 não consegue separar a nota certa da vizinha por limiar. O custo é retrabalho: o agente não acha a armadilha ou a decisão que já está no vault, ou lê notas irrelevantes e gasta tokens.

## Evidence

- Golden set, split `dev`, 19 positivas e 13 negativas: nenhum limiar de cobertura cumpre success@5 ≥ 0,80 e FP ≤ 0,20 ao mesmo tempo. Com cobertura ≥ 0,30: success@5 = 0,79 e FP = 0,31 ([[F0 - Linha de Base de Tokens e Golden Set MVP]], 2026-10-14).
- As três falhas de recuperação da F0 eram lacuna de vocabulário (mesma nota F0).
- Reescrita de query e julgamento pelo agente são os mecanismos centrais do agentic RAG ([[LangChain - Agentic RAG com LangGraph]], [[Yan et al 2024 - CRAG]]).
- Assumption: o agente segue um protocolo de busca escrito como regra binária. Validação: observar sessões reais depois da Fase 2 ([[Regra Gradual é Ignorada pelo Agente, Regra Binária é Obedecida]]).

## Proposed Solution

Transformar a busca do vault num loop agêntico barato, sem índice novo e sem LLM em tempo de hook. O agente ganha uma ferramenta de busca com saída estruturada (`sb search --json`) e um protocolo binário de busca no `SKILL.md` (rotear, reescrever, julgar pelo manifest, teto de tentativas, citar). Um adaptador de eval mede se reescrever a query melhora o ranqueador, com reformulações geradas uma vez por Haiku e gravadas em arquivo. Alternativas descartadas: embeddings (gate da F4 ainda não justifica), LLM no hook L1 (latência acima de 0,3 s), multiagente (custo de cerca de 15 vezes).

## Key Hypothesis

We believe que reescrever a query com o vocabulário provável das notas e unir os resultados por RRF will fechar a lacuna de vocabulário do ranqueador for o agente que consulta o vault.
We'll know we're right when o adaptador `rewrite` cumprir, no split `dev`, success@5 ≥ 0,80 e FP ≤ 0,20 com um mesmo limiar, sem piorar tokens por acerto em relação ao `rank`.

## What We're NOT Building

- Ativação do L1: o hook continua em sombra (decisão D-A1 do usuário, 2026-10-22).
- LLM em tempo de execução de hook ou de `sb search`: o LLM roda só uma vez, para gerar `rewrites.jsonl`.
- Embeddings, FTS5 ou índice novo: continuam atrás do gate da F4.
- Rerank por LLM (A4 do estudo): decidir depois da A3.
- Treino de modelo (Self-RAG, Search-R1) e multiagente.

## Success Metrics

Pisos escritos **antes** da medição (princípio 8 da RFC-001), aprovados pelo usuário em 2026-10-22.

| Metric | Target | How Measured |
|--------|--------|--------------|
| success@5 do `rewrite` no `dev` | ≥ 0,80 | `run_eval.py --methods rank,rewrite --split dev --k 5` |
| FP em negativas do `rewrite`, mesmo limiar | ≤ 0,20 | mesma execução, 13 negativas `q031`–`q042` mais as originais |
| tokens por acerto | ≤ o do `rank` no mesmo limiar | coluna do `run_eval.py` |
| Saída TSV de `sb search` | Byte a byte igual à de antes | teste de regressão na Fase 1 |
| Adesão ao protocolo | TBD - needs research | observar sessões reais; sem métrica automática na v1 |

Se o `rewrite` não cumprir os pisos, o resultado é registrado e o L1 continua em sombra. O protocolo da Fase 2 vale mesmo assim, porque o agente julga o resultado e não depende de limiar.

## Open Questions

- [ ] O limiar de cobertura do `rewrite` deve valer por variante (antes da fusão) ou sobre a cobertura máxima entre as variantes? O planejador da Fase 3 decide e justifica.
- [ ] O split `test` só deve ser rodado uma vez, depois de fixar o limiar no `dev`. Quem aprova essa rodada? Proposta: o usuário.
- [ ] O `claude -p` com Haiku respeita o modelo pedido e roda sem prompt interativo nesta máquina? Verificar no início da Fase 3.

---

## Users & Context

**Primary User**
- **Who**: o agente de código (Claude Code) que trabalha em qualquer projeto do usuário e consulta `~/obsidian_vault`; indiretamente, o usuário, que paga os tokens.
- **Current behavior**: grep nos manifests ou `sb search`, que devolve TSV `score, path, title`; abre notas sem critério de parada.
- **Trigger**: o agente vai decidir algo que o vault talvez já cubra (armadilha, padrão, decisão).
- **Success state**: acha a nota certa em até 3 aberturas, ou declara "o vault não cobre isso".

**Job to Be Done**
When o agente começa uma tarefa que o vault talvez cubra, I want to achar a nota certa com poucas buscas e poucas leituras, so I can não repetir um erro já registrado nem gastar tokens com notas vizinhas.

**Non-Users**
O usuário no app Obsidian (usa a busca do app) e agentes sem shell.

---

## Solution Detail

### Core Capabilities (MoSCoW)

| Priority | Capability | Rationale |
|----------|------------|-----------|
| Must | `sb search --json` com `path`, `title`, `type`, `summary`, `coverage`, `confidence`, `score`, `terms` | O agente julga pelo manifest sem abrir a nota |
| Must | Protocolo de busca binário no Behavior 1 do `SKILL.md` | É o loop agêntico; vale sem esperar a medição |
| Must | Adaptador `rewrite` + `rewrites.jsonl` gerado por Haiku | Testa a hipótese com número |
| Should | Gerador de reformulações reexecutável e idempotente | Novas queries do golden set ganham reformulação sem refazer as antigas |
| Could | `sb search` aceitar várias queries e fundir por RRF | Ferramenta para o passo 2 do protocolo; só depois da A3 provar ganho |
| Won't | Rerank por LLM, embeddings, L1 ativo | Ver "What We're NOT Building" |

### MVP Scope

Fases 1 a 3 abaixo. O MVP está completo quando o `run_eval.py` reportar `rank` e `rewrite` lado a lado no `dev` e o protocolo estiver no `SKILL.md`.

### User Flow

1. O agente roteia: nome próprio usa `grep` literal; tema usa `sb search --json`; pergunta global começa pelo MOC.
2. O agente reescreve a query em PT e EN e roda a busca.
3. O agente lê `title` e `summary` e abre no máximo 3 notas.
4. Se nada servir, reformula no máximo 2 vezes e depois diz "o vault não cobre isso".
5. O agente cita o path e mostra o `confidence` de cada nota usada.

---

## Technical Approach

**Feasibility**: HIGH. Tudo é Python stdlib e bash sobre arquivos que já existem.

**Architecture Notes**
- `run_search` (`00_META/skills/second-brain-sync/scripts/sb.py:296`) só repassa a saída do `vault_rank.sh`. O `--json` deve chamar o `vault_rank.sh` com `-n` (coluna de termos) e juntar as colunas do manifest por `path`.
- O manifest (`00_META/manifests/by_type/*.md`) tem as colunas `Path | Title | Tags | Created | Provenance | Confidence | Seen in | Summary`. O `type` vem do nome do arquivo do manifest. Reusar o parser que o `sb.py` ou o `run_eval.py` já tiverem; não criar um terceiro.
- O contrato do `vault_rank.sh` (cabeçalho do script) não muda. O ranqueador continua único: L1, `note_candidates.sh`, `run_eval.py` e `sb search` chamam o mesmo script.
- O `RankAdapter` (`00_META/eval/run_eval.py:97`) é o molde do `RewriteAdapter`. A cobertura vem do `vault_rank.sh -c`.
- A fusão usa reciprocal rank fusion com k = 60 sobre a query original mais as reformulações.
- O gerador de reformulações envia **só o texto da query** ao Haiku, nunca paths, títulos ou notas relevantes. Senão o eval vaza o gabarito.
- `rewrites.jsonl`: uma linha por query, `{"id", "query", "rewrites": [...], "model", "created"}`. O adaptador falha alto se faltar a linha de uma query, e falha alto se o texto de `query` divergir do golden set.

**Technical Risks**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Vazamento do gabarito no prompt do Haiku | M | Prompt só com a query; teste que verifica o prompt montado |
| Limiar ajustado no próprio `dev` superestima o ganho | H | Reportar IC95; rodar o `test` uma vez, com aprovação |
| `--json` muda a saída TSV por engano | L | Teste de regressão byte a byte |
| Protocolo vira regra gradual e é ignorado | M | Regras binárias, numeradas, com teto numérico |
| Reformulações do Haiku variam entre execuções | M | Gerar uma vez, gravar `model` e `created`, nunca regenerar linha existente |

---

## Implementation Phases

| # | Phase | Description | Status | Parallel | Depends | PRP Plan |
|---|-------|-------------|--------|----------|---------|----------|
| 1 | A1 — `sb search --json` | Saída estruturada para o agente julgar pelo manifest | complete (`7f4e0c4` em `feat/agentic-rag`, 225 testes OK, revisado em 2026-10-22) | - | - | `.claude/PRPs/plans/a1-sb-search-json.plan.md` (worktree) |
| 2 | A2 — Protocolo de busca agêntica | Regras binárias no Behavior 1 do `SKILL.md` | in-progress | - | 1 | `.claude/PRPs/plans/a2-protocolo-busca.plan.md` (worktree) |
| 3 | A3 — Adaptador `rewrite` | `gen_rewrites.py` + `rewrites.jsonl` + `RewriteAdapter` com RRF + medição | pending | - | 1 | - |

### Phase Details

**Phase 1: A1 — `sb search --json`**
- **Goal**: dar ao agente uma ferramenta de busca que devolve ponteiros com resumo, sem abrir notas.
- **Scope**: flag `--json` em `sb search` (lista JSON em stdout, uma entrada por resultado, campos da tabela MoSCoW); sem `--json`, saída idêntica à atual; testes em `test_sb.py` com manifest de teste; atualizar a linha do `sb search` no `SKILL.md` e na docstring do `sb.py`.
- **Success signal**: testes novos e os 29 existentes passam; teste de regressão do TSV passa; `sb search --json "importar issues jira"` devolve JSON válido com `summary` preenchido.

**Phase 2: A2 — Protocolo de busca agêntica**
- **Goal**: transformar a leitura do vault num loop com roteamento, reescrita, julgamento, teto e citação.
- **Scope**: reescrever o Behavior 1 do `00_META/skills/second-brain-sync/SKILL.md` com as 6 regras da §4 do [[Estudo - Agentic RAG no Second Brain]], em regras binárias e numeradas; manter os passos que já existem (manifest-first, um hop de wikilink); citar `sb search --json`. Não mexer em outros Behaviors.
- **Success signal**: o usuário aprova o texto antes do commit; nenhuma regra usa "prefira" ou "quando possível" sem teto numérico.

**Phase 3: A3 — Adaptador `rewrite`**
- **Goal**: medir se a reescrita de query fecha a lacuna de vocabulário.
- **Scope**: `00_META/eval/gen_rewrites.py` (chama `claude -p --model haiku` uma vez por query sem linha, 2 a 3 reformulações em PT e EN, idempotente, `--dry-run` que mostra os prompts); `00_META/eval/rewrites.jsonl` gerado e commitado; `RewriteAdapter` em `run_eval.py` com RRF e `--min-coverage`; testes sem rede (Haiku simulado); relatório no `dev` com `rank` e `rewrite` em vários limiares; registrar o resultado na nota [[F0 - Linha de Base de Tokens e Golden Set MVP]] como nova seção datada.
- **Success signal**: tabela `rank` contra `rewrite` registrada no vault, com veredito explícito contra os pisos de Success Metrics. O veredito pode ser negativo: registrar é o critério, não passar.

### Parallelism Notes

As Fases 2 e 3 dependem só da Fase 1 e tocam arquivos diferentes (`SKILL.md` contra `00_META/eval/`). Por decisão do usuário (D-A3), rodam em sequência: 1, 2, 3.

---

## Execução por agentes

Decisão do usuário (2026-10-22): cada plano é escrito por um agente **Opus novo**, e cada implementação por um agente **Sonnet**. A sessão principal só orquestra e revisa.

**Ambiente.** Worktree `~/obsidian_vault-wt/agentic-rag` na branch `feat/agentic-rag`, criada a partir do `master`. O checkout principal `~/obsidian_vault` fica no `master` para o `sb sync` continuar a funcionar. Um commit por fase, em Conventional Commits, sem `Co-Authored-By`. No fim, merge fast-forward no `master` e push, feito pela sessão principal.

**Planos.** Em `<worktree>/.claude/PRPs/plans/a<N>-<nome>.plan.md` O `.gitignore` do vault não cobre `.claude/`. A linha `/.claude/PRPs/` em `.git/info/exclude` (local, vale para todos os worktrees) mantém os planos fora do git e do `sb sync` (corrigido em 2026-10-22, apontado pelo planejador da A1).

**Brief do planejador (Opus), por fase:**

> Você vai escrever o plano da Fase {N} do PRD `40_Projects/second_brain_memory/PRD-003 - Agentic RAG no Second Brain.md`, no worktree `~/obsidian_vault-wt/agentic-rag`. Leia o PRD inteiro e os arquivos citados em Technical Approach. Siga o template do `/prp-plan` (`~/.claude/plugins/marketplaces/ecc/pi/core/commands/prp-plan.md`). Somente leitura: não edite código. Grave o plano em `.claude/PRPs/plans/a{N}-{nome}.plan.md`. O plano deve listar arquivos e linhas a tocar, testes a escrever primeiro, comandos de validação (`python3 -m pytest` nos arquivos de teste citados) e o critério de pronto da fase. Resolva as Open Questions da sua fase e justifique em uma linha cada. Devolva: path do plano e até 10 linhas de resumo, sem dump.

**Brief do implementador (Sonnet), por fase:**

> Implemente o plano `.claude/PRPs/plans/a{N}-{nome}.plan.md` no worktree `~/obsidian_vault-wt/agentic-rag` (branch `feat/agentic-rag`). Escreva os testes antes do código. Toque só os arquivos do plano. Rode os testes da fase e os testes existentes do mesmo diretório. Não rode `sb sync`, `git push` nem merge. Faça um commit da fase em Conventional Commits, sem `Co-Authored-By`. Devolva: hash do commit, saída resumida dos testes e qualquer desvio do plano, em até 15 linhas.

**Portões da sessão principal:** revisar o plano antes de liberar o implementador; revisar o diff antes da fase seguinte; na Fase 2, mostrar o texto ao usuário antes do commit; na Fase 3, conferir o prompt do `gen_rewrites.py --dry-run` antes de gastar chamadas ao Haiku.

---

## Decisions Log

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| D-A1 papel do L1 | Continua em sombra | Uma linha de aviso; aposentar | Esperar números da A3 (usuário, 2026-10-22) |
| D-A2 LLM no eval | `claude -p` com Haiku, uma vez | Sem LLM; LLM por execução | Custo único e eval determinístico (usuário, 2026-10-22) |
| D-A3 ordem | A1, A2, A3 | A3 antes da A2 | A2 entrega valor sem medição (usuário, 2026-10-22) |
| Local do PRD | Nota no vault | `.claude/PRPs/prds/` | Fica no manifest e no grafo (usuário, 2026-10-22) |
| Piso da A3 | Pisos do gate do L1 | Ganho relativo sobre o `rank` | Mesmo critério que o `rank` não cumpriu (usuário, 2026-10-22) |
| Execução | Plano por Opus novo, código por Sonnet | Sessão principal faz tudo | Usuário, 2026-10-22 |
| Git | Branch e merge local | PR no GitHub | Mesmo fluxo das etapas I1–I4 (usuário, 2026-10-22) |

---

## Research Summary

**Market Context**
O agentic RAG troca o pipeline fixo por um loop em que o LLM decide se busca, reescreve e julga ([[Singh et al 2025 - Survey de Agentic RAG]]). Busca agêntica sem vetor (grep, glob, Read) é a abordagem do Claude Code ([[Anthropic 2025a - Effective Context Engineering]]). Para pergunta simples, o loop não compensa ([[Jeong et al 2024 - Adaptive-RAG]]). 22 fontes estão em `10_Literature_Notes/References/`, ligadas por [[Agentic RAG]].

**Technical Context**
O vault já tem os blocos: manifests com `summary`, ranqueador único com cobertura, golden set de 42 queries, `run_eval.py` com adaptadores e IC95. Falta o loop (protocolo) e a medição da reescrita.

---

*Generated: 2026-10-22*
*Status: DRAFT - needs validation*
