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

## Atualização 2026-10-14: F0b e F1a executadas

**F0b (restaurar a decisão do ECC).** Com aprovação do usuário, `ecc@ecc` passou a `false` no escopo `user`
(`~/dotfiles/claude/settings.json:159`, editado direto no arquivo do repo para não acionar a armadilha do plugin CLI) e o
link `~/.claude/rules/ecc-common` foi removido. Ressalva: a ativação global **não foi acidente do CLI**; o commit
`a40e8a7` (2026-10-05, no dotfiles) a fez de propósito ("enable ecc plugin ... now loaded globally"), depois da decisão do
vault de 2026-09-30. A restauração segue a decisão registrada, mas vale o usuário confirmar que não quer o ECC global.
O efeito vale numa sessão nova; o M1 pós-mudança ainda precisa ser medido com `usage_baseline.sh`. O arquivo do dotfiles
tem outras alterações do usuário sem commit; nada foi commitado lá.

**F1a (coluna `summary`).** `generate_manifests.py` ganhou a coluna `Summary` por último (≤ 160 caracteres, primeiro
parágrafo em prosa do corpo, markdown removido, sem LLM), escape de `|` (trocado por `¦`, porque os consumidores em
`awk -F'|'` quebrariam com `\|`) e escrita atômica. A saída do `session_hint.sh` ficou idêntica nos três repos testados.
Os 290 manifests têm resumo; 11 testes novos passam.

Desvio da RFC §4.1: usei **só o primeiro parágrafo**, não "primeira frase em negrito". Em amostra, o negrito costuma ser
um fragmento ("não serve"), pior que o parágrafo. Registrar na RFC se o usuário aceitar.

| `rank` no split dev, k=5 | success@5 | IC95 | MRR | nDCG@5 | tokens/acerto |
|---|---|---|---|---|---|
| sem `summary` (F0c) | 0,84 | 0,68–1,00 | 0,80 | 0,79 | ≈ 2,2 mil |
| com `summary` (F1a) | 0,89 | 0,74–1,00 | 0,89 | 0,88 | ≈ 1,8 mil |

A diferença é de **uma query** em 19, dentro do intervalo de confiança: não prova ganho, só não indica piora. Restam as
falhas `q008` (Taste vs impeccable) e `q016`. A decisão de manter ou reverter o `summary` continua dependendo dos 60 pares
(RFC §8). O split `test` segue sem uso.

## Atualização 2026-10-14: F1b (hook em sombra) e calibração do limiar

**Golden set.** O usuário aprovou as 30 queries originais (`validated: true`, `source: llm-draft+user-approved`).
Acrescentei 12 negativas no split `dev` (`q031`–`q042`, `validated: false`) só para calibrar o limiar de silêncio, porque
o `dev` tinha uma única negativa. Várias são vizinhas de notas reais do vault (deploy, testes, datas), então o falso
positivo medido é pessimista: mostrar uma nota adjacente pode ser útil.

**Entregue.** `prompt_hint.sh` (corpo do hook), `vault_rank.sh` com os campos `coverage` e `confidence` e as opções
`-c` (cobertura mínima) e `-t` (mínimo de termos úteis), harness com `--min-coverage`/`--min-terms`, 13 testes novos
(sem rede, com manifest de teste). O wrapper `~/dotfiles/claude/hooks/second-brain-prompt-hint.sh` está registrado em
`UserPromptSubmit` e **inerte** até `SECOND_BRAIN_PROMPT_HINT=shadow` ser definido. O `SessionStart` (L0) agora compara
caminho exato (um irmão como `obsidian_vault2` não casa mais) e grava o que mostrou no arquivo de dedupe do L1.

**Cobertura** é a fração do peso idf dos termos da query que a nota casa (termo ausente do vault conta como não casado).
Separa melhor que a pontuação bruta, que cresce com o tamanho da query: uma negativa chegou a 22 e uma positiva certa
a 10,7.

| `rank`, dev, k=5 (19 positivas, 13 negativas) | success@5 | FP em negativas | tokens/acerto |
|---|---|---|---|
| sem limiar | 0,89 | 1,00 | ≈ 4,3 mil |
| cobertura ≥ 0,25 | 0,79 | 0,46 | ≈ 2,7 mil |
| cobertura ≥ 0,30 (padrão do hook) | 0,79 | 0,31 | ≈ 1,8 mil |
| cobertura ≥ 0,35 | 0,74 | 0,23 | ≈ 1,3 mil |

**Nenhum limiar cumpre os dois pisos ao mesmo tempo** (success@5 ≥ 0,80 e FP ≤ 0,20). Os pisos não foram afrouxados.
Consequência: o L1 **não passa o gate** com um ranqueador lexical puro e permanece em sombra. O limiar 0,30 é provisório,
escolhido sobre o próprio `dev` (32 pontos), logo otimista. O log de sombra guarda os cinco candidatos com pontuação e
cobertura por prompt, o que permite reajustar o limiar sem rodar o hook de novo. Próximas alavancas, em ordem de custo:
dados reais do log, depois bônus de frase/bigrama no ranqueador, depois a decisão sobre embeddings (F4) com dados em mãos.

**Latência** do hook inteiro: 0,18–0,27 s (ranqueador ≈ 0,13 s), dentro do piso de 0,3 s mas sem folga; `timeout 0,3` no
ranqueador faz o hook calar sob carga em vez de atrasar o prompt. **Privacidade:** o log de sombra guarda os primeiros 300
caracteres de cada prompt em `~/.local/state/second-brain/shadow.jsonl` (arquivo 0600, diretório 0700, nada sai da máquina).

## Atualização 2026-10-14: validação independente da F1b e F2

**Validação.** Um revisor independente (somente leitura) rodou os testes e tentou quebrar o hook. Não quebrou: JSON
inválido, `jq` ausente, injeção por prompt (`$(...)`, crase, bytes inválidos), `session_id` com `../`, 40 hooks
concorrentes e estado ilegível terminam sempre em saída vazia e `exit 0`, com log íntegro e permissões 0600/0700.
Achados corrigidos (com teste de regressão cada):

| Achado | Correção |
|---|---|
| Timeout do ranqueador (0,3 s) estourava sob carga e o log gravava `candidates: []`, indistinguível de "sem match" | Teto de 0,6 s e campo `timeout: true` no log |
| Prompt de 5 MB deixava o hook em 1,9 s | Leitura de entrada limitada a 256 KB e só os 2.000 primeiros caracteres vão ao ranqueador |
| Só título e resumo eram escapados no manifest; `\|` em path ou tags deslocava as colunas | Todas as colunas passam por `escape_cell` (hoje 0 linhas com número de colunas errado) |
| Título só com espaços deslocava campos; títulos vinham com aspas literais (gastam token) | Título sem aspas externas e, se vazio, o nome do arquivo |
| `cwd` ausente com prompt vazio virava `session_id` como prompt | Sentinela no `jq` |
| `shadow.jsonl` sem rotação | Acima de 5 MB mantém só as 2.000 últimas linhas |

Limitação conhecida, sem correção: o `sed` do L0 que grava o `.seen` é guloso; um path com ` — ` no nome ficaria truncado.
Nenhum path do vault atual tem isso.

**F2 entregue.** `note_candidates.sh "<título>" "<tags>"` lista até 3 notas que já cobrem o assunto (mesmo ranqueador,
cobertura ≥ 0,25) e grava cada chamada em `note_candidates.jsonl`. O `vault_sync.py` agora impõe a regra em código:
(1) `flock` em `.git/second-brain-sync.lock`, esperando até 120 s; (2) nota **nova** com cobertura ≥ 0,5 contra uma
existente é recusada, a menos que venha `--new-because "<uma linha>"`; (3) nota nova de agente
(`provenance` diferente de `manual`) precisa de `confidence: low`; (4) cada execução grava uma linha em `sync.jsonl`
(`created`, `updated`, `new_because`, `outcome`). `SKILL.md` e `Frontmatter-Schema.md` foram alinhados. 12 testes
novos usam vault git real e remoto bare temporários.

**Calibração do 0,5** (nada validado): das 170 notas permanentes, 53 (31%) têm outra nota com cobertura ≥ 0,5 usando
título e tags como query, e 42 com ≥ 0,6. Isso mede vizinhança temática, não duplicata, então o bloqueio pode incomodar
mais que o necessário; o custo é uma linha `--new-because`. O critério de saída da F2 ("nenhuma criação com candidato
ignorado") passa a ser verificável em `sync.jsonl` e `note_candidates.jsonl`, mas só terá número depois de uso real.

## Atualização 2026-10-15: validação das negativas, veredito dos pisos e F3

**Aprovações do usuário.** As 12 negativas dev `q031`–`q042` foram validadas (`validated: true`, `source: llm-draft+user-approved`).
O veredito sobre o gate do L1 foi aceito: o ranqueador lexical não cumpre os dois pisos ao mesmo tempo (success@5 ≥ 0,80
e falso positivo ≤ 0,20), então o L1 permanece em sombra e a recalibração depende dos dados reais do `shadow.jsonl`.
O piso do M5 continua a fixar antes de qualquer ativação.

**Dotfiles.** O `master` recebeu a branch do hook em sombra por fast-forward (`b217340`, `bd3bdb3`). Nada foi enviado
ao remoto: o `master` local está à frente de `origin/master`. As alterações pessoais do usuário em `settings.json` e
`zsh/.zshrc` continuam sem commit.

**F3 (trilha B).** `make ecc-status` já existia e passou a informar o estado efetivo (local, projeto ou usuário), com a
opção `--short`. O hook de `SessionStart` imprime uma linha (`ECC desligado (usuário). Só o usuário muda ...`, cerca de
20 tokens), mesmo quando o vault não tem dica para o projeto. O `AGENTS.md` ganhou o contrato: o agente só liga ou
desliga o ECC se o usuário pedir, sugere ligar para revisão Go/Java/Kotlin, `orch-review` e `review-pr`, e não usa
agentes `ecc:*` com o plugin desligado. Commit `cb6cfb1` na branch `feat/ecc-session-status` do dotfiles, sem push e sem
merge. Ficou de fora desta etapa: resolver os conflitos entre `rules/common` e o `AGENTS.md`, que só importam nos
projetos em que o ECC for ligado com rules completas (o `ecc-common` global já foi removido na F0b).

## Próximos passos

1. **Você**: validar ou reescrever as 30 queries (principalmente as 21 `paraphrase`), e aprovar ou ajustar
   os pisos e o protocolo do M4.
2. **F0b** (confirmar): restaurar `ecc@ecc: false` no escopo `user` e remover `ecc-common`; medir M1 com
   `usage_baseline.sh` numa sessão nova.
3. **F1a**: coluna `summary` no manifest; reexecutar o `run_eval.py` e comparar com esta tabela.
