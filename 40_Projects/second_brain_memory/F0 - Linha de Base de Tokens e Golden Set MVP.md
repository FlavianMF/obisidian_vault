---
title: F0 — Linha de Base de Tokens e Golden Set MVP (resultados)
type: project
tags: [rfc, agentic-ai, second-brain, tokens, baseline, golden-set, evaluation, claude-code]
created: 2026-10-14
provenance: obsidian_vault
project: second_brain_memory
confidence: low
verified: 2026-10-14 via claude plugin details, transcripts de ~/.claude/projects (campo usage) e run_eval.py (split dev)
scope: project
---

# F0 — Linha de Base de Tokens e Golden Set MVP (resultados)

Resultado das etapas **F0a** (linha de base M1/M4) e **F0c** (golden set MVP + harness) da
[[RFC-001 - Memória de Agentes sobre o Second Brain com Orçamento de Tokens]]. Nenhuma
configuração foi alterada: a F0b (passo ECC) segue pendente de confirmação.

## F0a — Linha de base de tokens

### M1 — custo fixo por sessão

Medido com `claude plugin details <plugin>` (campo *Always-on*, estimativa do próprio Claude Code):

| Plugin | Always-on (tokens) |
|---|---|
| `ecc@ecc` (71 agents, 311 skills, 97 shims de comando) | ~47.561 |
| `figma@claude-plugins-official` | ~2.135 |
| `caveman@caveman` | ~1.832 |
| `mattpocock-skills@claude-plugins-official` | ~1.611 |
| `impeccable@impeccable` | ~529 |
| `typesafe@typesafe-ai` | ~209 |
| `github`, `playwright`, `fast-jev-compaction` | ~0 |
| **Soma dos plugins** | **~53.877** |

Regras carregadas em todo turno: `~/.claude/CLAUDE.md` (1,2 KB) + `AGENTS.md` (5,0 KB) +
`~/.claude/rules/ecc-common` (17,6 KB, symlink para `vendor/ecc/upstream/rules/common`).
Estimativa: ≈ 1,8 mil tokens as duas primeiras e ≈ 4,4–5,0 mil a última (bytes ÷ 4 a ÷ 3,5).

Contexto da **primeira mensagem** de cada sessão com transcript (soma de `input_tokens`,
`cache_creation_input_tokens` e `cache_read_input_tokens` da primeira resposta; inclui o
primeiro prompt e os hooks de `SessionStart`, logo é teto do custo fixo):

| Sessão | Projeto | Contexto na 1ª mensagem |
|---|---|---|
| aa7d55e8 | dotfiles | 42.986 |
| f7934048 | obsidian_vault | 57.883 |
| 2af20811 | obsidian_vault | 57.945 |
| 55ce7e3f (esta) | obsidian_vault | 71.892 |

Só há 4 transcripts disponíveis, então **não dá para separar o efeito do ECC**: a sessão de
dotfiles pode ter rodado com o plugin desligado ou em outra versão. O M1 comparável antes/depois
da F0b sai de `00_META/eval/usage_baseline.sh <transcript>` numa sessão nova, sem precisar de
`/context` (o script lê só campos numéricos de `usage`, nunca conteúdo).

### M4 — custo por tarefa (esta sessão, thread principal, 80 mensagens do assistente)

| Medida | Tokens |
|---|---|
| `output_tokens` | 250.604 |
| `cache_read_input_tokens` | 10.890.122 |
| `cache_creation_input_tokens` | 390.626 |
| `input_tokens` (sem cache) | 162 |
| Contexto médio por turno (cache_read ÷ 80) | ≈ 136 mil |

Leituras:
- **O volume é dominado por releitura de cache**: cada token que fica na janela é reprocessado a
  cada turno. Por estimativa, as ~47,5 mil do ECC × 80 turnos ≈ 3,8 milhões de leituras de cache,
  **cerca de 35% do total de 10,9 milhões**. Slimming de contexto fixo rende por turno, não uma vez.
- Em unidades "equivalente a entrada" pelos multiplicadores de tabela (escrita ×1,25, leitura ×0,1;
  premissa: preços de lista de 5 min, a conferir): ≈ 1,58 milhão. Saída não entra nessa conta.
- Os subagentes (sidechain) ficaram fora; o custo real da sessão é maior.

**Protocolo proposto para o M4 comparável** (a aprovar): 5 tarefas reais e repetíveis, escolhidas
pelo usuário (ex.: retomar uma decisão registrada no vault; aplicar uma armadilha conhecida; abrir
nota nova sobre um tema já coberto), cada uma com a **mesma redação de prompt**, rodadas com o L1 em
`shadow` (controle) e em `active`, em sessão nova e limpa. Métrica: soma de
`input + cache_creation×1,25 + cache_read×0,1` e nº de notas lidas, via `usage_baseline.sh`. Com 5
tarefas o resultado é indicativo, não estatístico.

## F0c — Golden set MVP

Entregue em `00_META/eval/`: `golden.jsonl` (30 queries), `run_eval.py` (harness), `test_run_eval.py`
(15 testes `unittest`, todos passam; `pytest` não está instalado, então usei a biblioteca padrão) e
`usage_baseline.sh`. O ranqueador de produção é `00_META/skills/second-brain-sync/scripts/vault_rank.sh`
(grep/awk, query por `ENVIRON`, acentos normalizados, ≈ 130 ms por chamada, dentro do orçamento de 300 ms).

Composição: 27 positivas (5 `lexical`, 21 `paraphrase`, 1 `multihop`) e 3 negativas; 20 em `dev` (19
positivas, 1 negativa) e 10 em `test`. Todos os 27 rótulos foram conferidos contra o sistema de arquivos (o teste do harness falha se
um rótulo apontar para nota inexistente).

### Resultado (split `dev`, k=5, 19 positivas e 1 negativa)

| método | success@5 | IC95 | recall@5 | MRR | nDCG@5 | FP em negativas | tokens/acerto |
|---|---|---|---|---|---|---|---|
| `rank` (produção) | 0,84 | 0,68–1,00 | 0,82 | 0,80 | 0,79 | 1,00 | ≈ 2,2 mil |
| `random` (baseline degenerado, 200 sorteios) | 0,02 | 0,02–0,02 | 0,02 | 0,01 | 0,01 | 1,00 | ≈ 282 mil |
| `fixed` (baseline degenerado) | 0,00 | 0,00–0,00 | 0,00 | 0,00 | 0,00 | 1,00 | sem acerto |

`tokens/acerto` é estimativa (chars ÷ 3,5): linhas devolvidas pelo método mais o corpo das notas que o
agente abriria em ordem de ranking até o primeiro acerto de grau 2.

**Falhas do `rank` em k=5:** `q008` (Taste vs impeccable; nota-alvo não contém essas palavras),
`q016` (acerto na posição 7) e `q028` ("promessa adiada" contra *Deferred-Promise*, o inglês do título).
As três são **lacuna de vocabulário**, exatamente o que a coluna `summary` da F1a deve atacar.
`q019` acerta na posição 5. Essa é a evidência local mais forte a favor do manifest enriquecido antes de
qualquer embedding.

### O que este resultado **não** prova

- **As queries foram escritas por LLM, olhando os títulos das notas**, e ainda não foram validadas por
  você (`"validated": false`, `"source": "llm-draft"` em todas). A taxa de acerto está provavelmente
  **otimista** por vazamento lexical. Validar ou reescrever as queries é o primeiro passo antes de qualquer decisão.
- Com 19 positivas o IC95 vai de 0,68 a 1,00: só se distinguem métodos muito distantes.
- **Falso positivo em negativas = 1,00**: sem limiar, o ranqueador sempre devolve algo. O limiar de
  silêncio (princípio 2 da RFC) é trabalho da F1b e precisa ser calibrado em `dev`.
- O split `test` **não foi rodado** e não deve ser usado para ajustar nada; fica para a decisão final.
- Nenhum ajuste de ranking foi feito até aqui (os resultados são do primeiro run).

## Pisos propostos para o gate da §8 (a aprovar; escritos antes de rodar o L1)

| Critério | Piso | Origem |
|---|---|---|
| `success@5` do L1 em ≥ 60 pares (golden validado + log em sombra) | ≥ 0,80 | próximo do `rank` atual em `dev`; só vale com queries validadas |
| Falso positivo em negativas, com limiar de silêncio | ≤ 0,20 | hoje 1,00 sem limiar |
| Tokens injetados por prompt | ≤ 400 (≈ 90 esperado com 3 linhas) | RFC §4 |
| Latência do hook por prompt | ≤ 300 ms | medido ≈ 130 ms |
| M5 (injetado e depois lido) | **a fixar** | sem dado: só existe após as primeiras sessões em sombra; a regra é escrever o número **antes** de ativar |

O piso do M5 é a única lacuna em relação ao critério de saída da F0c ("pisos escritos"): não existe linha
de base para ele antes do hook rodar em sombra.

## Achado fora do escopo: o ECC já tem decisão no vault, e o estado atual desvia dela

[[ECC - Adotar Ideias, Não o Runtime]] (2026-09-30, `confidence: medium`) já decidiu: `ecc@ecc` instalado e
**desligado** no escopo de usuário, ligado por projeto com `make ecc-on DIR=…` (opção `NO_COMMON=1`), hooks
em perfil `minimal`. O estado atual é `"ecc@ecc": true` (`~/.claude/settings.json:159`) e o link
`~/.claude/rules/ecc-common` existe desde 2026-10-14 18:09. Isso é **desvio da decisão registrada**, não
decisão nova. Provável causa: [[Claude Plugin CLI Reescreve o settings.json Symlinkado do Repo]]. A F0b
deve ser tratada como **restaurar** o estado decidido, e a F3 como **estender** o `make` existente com
`status` e a linha de estado do `SessionStart`, sem criar comando paralelo.

## Próximos passos

1. **Você**: validar ou reescrever as 30 queries (principalmente as 21 `paraphrase`), e aprovar ou ajustar
   os pisos e o protocolo do M4.
2. **F0b** (confirmar): restaurar `ecc@ecc: false` no escopo `user` e remover `ecc-common`; medir M1 com
   `usage_baseline.sh` numa sessão nova.
3. **F1a**: coluna `summary` no manifest; reexecutar o `run_eval.py` e comparar com esta tabela.
