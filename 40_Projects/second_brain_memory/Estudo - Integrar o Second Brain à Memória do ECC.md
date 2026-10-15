---
title: Estudo — integrar o second brain à memória do ECC
type: project
tags: [study, ecc, second-brain, memory, agentic-ai, interactive, continuous-learning, tokens]
created: 2026-10-15
provenance: obsidian_vault
project: second_brain_memory
confidence: low
verified: 2026-10-15 via leitura do plugin ecc 2.2.3 (cache local) e dos arquivos do vault e dos dotfiles por três agentes ecc:code-explorer, sem executar nada
scope: project
---

# Estudo — integrar o second brain à memória do ECC

> Estudo em cinco etapas, pedido em 2026-10-15: entender o sistema de memória do ECC, pegar o que ele tem de método
> interativo e de integração e aplicar **a nossa versão** sobre o second brain. **Decisão do usuário (2026-10-15):** o second
> brain terá **runtime próprio, em arquitetura híbrida** (runtime nosso como fonte da verdade mais um adaptador para o formato
> `ecc.memory.v1` do ECC); isso emenda a decisão de 2026-09-30 e a leitura da D10 (seção 3). Nada foi implementado. Tudo que veio do ECC
> foi lido como dado de terceiros. Itens marcados **NÃO VERIFICADO** são inferência ou ficaram sem confirmação no código.
> Relaciona-se a [[RFC-001 - Memória de Agentes sobre o Second Brain com Orçamento de Tokens]], à decisão
> [[ECC - Adotar Ideias, Não o Runtime]] e ao [[PRD-002 - ECC Automático para Web e C e Linha de Status]].

## Etapas do estudo

| Etapa | Pergunta | Resultado |
|---|---|---|
| S1 | Que mecanismos de memória, aprendizado e continuidade o ECC tem? | Seção 1 |
| S2 | Quais métodos interativos e pontos de integração existem? | Seção 2 |
| S3 | O que o second brain já tem, e o que a integração não pode violar? | Seção 3 |
| S4 | O que adotar, adaptar ou rejeitar? | Seção 4 (matriz) |
| S5 | Qual é a nossa versão, com etapas, métricas e gates? | Seção 5 |

## 1. S1 — o que o ECC tem (v2.2.3)

**Nada do aprendizado roda no perfil do usuário.** O plugin fica desligado no escopo de usuário e, quando ligado por projeto,
roda com `ECC_HOOK_PROFILE=minimal` e `ECC_DISABLED_HOOKS=stop:evaluate-session,post:ecc-metrics-bridge`. Em `minimal` só rodam o
`session-start` (injeção) e o `stop:session-end` (resumo de sessão). A observação contínua (instincts), o `pre-compact`, o
`suggest-compact` e o `skill-health` pertencem aos perfis standard e strict.

| Mecanismo | O que faz | Interativo? | Armazenamento | Qualidade | No nosso perfil |
|---|---|---|---|---|---|
| `session-end` + `session-start` | resume a sessão a cada Stop (mecânico; LLM Haiku quando o contexto restante < 20% ou a cada 50 mensagens) e injeta o resumo mais recente no `startup` (≤ 7 dias, teto de 8000 caracteres, envelope "HISTORICAL REFERENCE ONLY") | não | `~/.claude/session-data/*-session.tmp`, por worktree | sem score; sem scrub de segredos encontrado | ativo se o plugin estiver ligado |
| `/save-session`, `/resume-session` | handoff com seções fixas: o que funcionou (com evidência), **o que NÃO funcionou**, o que não foi tentado, estado dos arquivos, decisões, bloqueios e **próximo passo exato** | semi: mostra o arquivo e pergunta "está correto?" | mesmo diretório | ranking de candidatos na retomada (rejeita placeholder) | só sob demanda |
| `/learn`, `/learn-eval` | extrai uma skill da sessão; o `learn-eval` roda um checklist por leitura real (grep no acervo e na memória) e dá **um veredito**: Save, Improve then Save, Absorb into X ou Drop | sim: mostra caminho, checklist e diff e exige confirmação (Drop não pede) | `~/.claude/skills/<slug>/SKILL.md` | valida slug, YAML e "Use when" depois de gravar; redige segredos e PII | só sob demanda |
| `continuous-learning-v2` (instincts) | observa cada tool call, um observer Haiku propõe instincts atômicos (gatilho, ação, evidência, confiança 0,3–0,85); injeta até 6 com confiança ≥ 0,7 | não na captura; `[y/N]` em import, promote e merge | `~/.local/share/ecc-homunculus/projects/<hash>/` | promoção quando o mesmo id aparece em ≥ 2 projetos com média ≥ 0,8; `pending/` expira em 30 dias | **inativo** (`exit 0` em minimal) |
| `unified-memory` (Memory Vault) | vault Markdown `ecc.memory.v1` com frontmatter (kind, scope, trust, status active/rejected/superseded, links), CLI `ecc memory` e MCP opt-in | não | `<repo>/.ecc/memory/`, `~/.ecc/memory/` | tudo entra como `trust: unreviewed`; só cria, nunca sobrescreve; `doctor` acusa IDs duplicados e links quebrados; rejeita segredos conhecidos antes de gravar | **inativo** (exige o runtime npm `ecc-universal`) |
| `ck` (Context Keeper) | `/ck:init|save|resume|forget`, contexto por projeto em JSON (resumo, onde parou, próximos passos, decisões, bloqueios) | sim (`yes/edit`) | `~/.claude/ck/` | backup na migração | só sob demanda |
| `skill-stocktake` | auditoria Quick (só o que mudou, por mtime) ou Full (lotes de ~20 por subagente, retomável) com veredito Keep, Improve, Update, Retire ou Merge | sim: confirmação por arquivo para Retire e Merge | `results.json` | reavalia só o que mudou | só sob demanda |
| `hookify` | analisa correções do usuário na conversa e propõe regras executáveis | sim (por regra aprovada) | `.claude/hookify.*.local.md` | — | ativo (runtime em minimal) |

**Fatos relevantes para a comparação**
- A "interatividade" do ECC é sempre texto (`[y/N]`, "yes/edit"); não há `AskUserQuestion` nos fluxos de memória.
- O decaimento semanal de confiança aparece **só no prompt do observer**; não há código de decaimento no `instinct-cli.py`
  (**NÃO VERIFICADO** se é aplicado). Quem escreve em `instincts/pending/` também é **NÃO VERIFICADO**.
- Rejeitar um item (`/learn`, `/promote`, `/instinct-import`) **não deixa registro**: a proposta pode voltar.
- Não existe gancho para plugar outra fonte de memória no SessionStart do ECC; a extensão real é um hook próprio com
  `additionalContext`, que é o que já fazemos. O Memory Vault, por decisão de design, **não** é injetado no SessionStart
  (recall explícito).
- Não achei métrica alguma de que a injeção de instincts melhore resultados.

## 2. S2 — métodos interativos e integração

Os quatro padrões de interação do ECC que valem como modelo (todos em texto, sem runtime):

1. **Veredito de quatro vias antes de gravar** (`/learn-eval`): rascunho, checklist de sobreposição por leitura real, veredito
   (Save, Improve then Save, Absorb into X, Drop), confirmação, validação pós-escrita.
2. **Handoff estruturado** (`/save-session`): seções fixas com evidência obrigatória e a seção "o que NÃO funcionou".
3. **Promoção por critério numérico com `[y/N]` e `--dry-run`** (`/promote`): mesmo id em ≥ 2 projetos, média ≥ 0,8, mostra
   origem e confiança, aceitar grava com `promoted_from` e `promoted_date`.
4. **Revisão em lote com cache e retomada** (`skill-stocktake`): só reavalia o que mudou, lotes pequenos, `batch_progress`
   retomável e confirmação por arquivo para ações destrutivas.

Pontos de integração: os dados ficam em arquivos locais (Markdown, YAML, JSONL, SQLite em `~/.claude/ecc/state.db` sem
instincts nem memória) e são manipulados por um CLI Python (`instinct-cli.py`); não há API de rede. As variáveis `ECC_*`
controlam teto de injeção e kill switch (`ECC_SESSION_START_CONTEXT=off`).

## 3. S3 — o nosso lado

**Já temos** (detalhes no RFC-001 e na nota F0): captura ao fim da tarefa com `note_candidates.sh` e `vault_sync.py`; armazenamento
em Markdown com frontmatter (`confidence`, `seen_in`, `verified`, `scope`); injeção L0 (≤ 5 linhas) e L1 (≤ 3 linhas, **em
sombra**); guardas em código (nota nova sempre `low`, promoção verificada contra o `HEAD`, recusa de duplicata, `flock`);
observabilidade em `~/.local/state/second-brain/` (`sync.jsonl`, `shadow.jsonl`, `<sid>.injected`, `<sid>.opened`) e a linha de status.

**Restrições que a integração não pode violar**
1. [[ECC - Adotar Ideias, Não o Runtime]] (2026-09-30): ECC desligado por padrão; `continuous-learning-v2` foi avaliado e
   **rejeitado** (log só de tool calls, observer em background, redação de segredos fraca, bugs abertos).
2. Fonte única é o vault (D11); local-first; **sem MCP novo de memória**; sem embeddings antes do gate da §8 (D7).
3. Orçamento de tokens: L0 ≤ 5 linhas, L1 ≤ 3 linhas (≤ 400 tokens, ≤ 300 ms); silêncio por padrão.
4. Escrita com portão (D6): atualizar antes de criar; nota nova `low`; sem `--force`; sem `git add -A`.
5. Memória recuperada é **dado, não instrução**; proveniência e confiança visíveis.
6. Segredos fora do contexto e de qualquer log novo.
7. Princípio 8: **sombra antes de ativo, com gate numérico**. Promoção para `Agent-Instruction.md` continua manual.

**Contradição resolvida pelo usuário:** a **D10 (Fechada)** do RFC diz "utilizar o `unified-memory` e o `continuous-learning-v2`
como base para ser aplicado no vault", o que contradizia a nota de decisão e o §1 do RFC (ambos fora da v1). O usuário
escolheu o **híbrido**: runtime próprio do second brain como fonte da verdade e um adaptador para o `unified-memory`
(`ecc.memory.v1`). O `continuous-learning-v2` (observer de tool calls) **continua rejeitado** até o usuário dizer o contrário;
a nota de decisão de 2026-09-30 e o §1 do RFC precisam ser emendados quando a I0 for aprovada.

**Lacunas do nosso lado:** captura só ao fim da tarefa (nada durante a sessão); nenhuma revisão em lote nem fila de
candidatos; obsolescência só como relatório (`--stale-report`); nenhuma realimentação do uso para `confidence`/`seen_in` (o M5 não
está agregado); nenhuma métrica de qualidade de **escrita**; uma nota `medium` sem evidência (`MB-249 - Guia de Estudo.md`).

## 4. S4 — matriz de adoção

Legenda: **Adotar** (ideia quase como está), **Adaptar** (ideia sobre o vault, com as nossas guardas), **Rejeitar**, **Adiar**.

| Ideia do ECC | Função | Decisão | Por quê / como fica no vault |
|---|---|---|---|
| Veredito Save / Improve / Absorb / Drop com checklist por leitura real (`/learn-eval`) | captura | **Adaptar** | O `note_candidates.sh` e o `vault_sync.py` já barram duplicata em código; falta o veredito explícito e **registrado**. Passo 2b do `SKILL.md` ganha o veredito e o `sync.jsonl` guarda `verdict`. Sem confirmação por nota: a escrita pelo agente sem aprovação é decisão do usuário. |
| Validação pós-escrita (slug, YAML, nome) | captura | **Adotar** | Já coberto pelo gerador de manifests e pelos testes; reforçar com checagem de frontmatter no `vault_sync.py`. |
| Rejeição de segredos antes de gravar (Memory Vault) | segurança | **Adotar** | Cheque por padrões de credencial no conteúdo das notas novas e alteradas, falhando fechado. Barato e atende a restrição 6. |
| `status` active/superseded + `supersedes`, `doctor` (IDs duplicados, links quebrados) | qualidade | **Adaptar** | Campo opcional `status` e `supersedes` no schema; um `vault_doctor` (só leitura) para wikilinks quebrados, títulos duplicados e frontmatter ausente. |
| Promoção por critério com `[y/N]` e `--dry-run` (`/promote`) | promoção | **Adaptar** | Fluxo interativo de revisão: candidatos com `seen_in` ≥ 2, `scope: global` e `confidence` ≥ medium; mostra evidência; **registra a rejeição** (o ECC não registra) para não repropor. Promoção para `Agent-Instruction.md` segue manual. |
| Revisão em lote com cache e retomada (`skill-stocktake`) | decaimento | **Adaptar** | Mesmo fluxo de revisão em modo "estoque": só notas alteradas ou vencidas (mtime e `verified` > 180 dias), lotes pequenos, estado retomável em `~/.local/state`, veredito Keep, Update, Merge ou Retire (= `status: superseded`), confirmação por nota. |
| `pending/` com TTL de 30 dias, aviso aos 7 e `prune` | captura durante a sessão | **Adaptar** | **Fila de candidatos fora do vault** (arquivo de estado por sessão), com expiração; resolve a lacuna "captura durante a sessão" sem violar a D8 (nada transitório entra no vault). |
| Captura de correções do usuário (`hookify`) | captura durante a sessão | **Adaptar** | Quando o usuário corrige o agente ou ele descobre uma armadilha, o agente acrescenta **uma linha** à fila de candidatos (regra no `AGENTS.md`). Sem observer, sem log de tool calls, sem chamada de modelo extra. |
| Instincts com confiança numérica, evidência e decaimento | qualidade | **Rejeitar o runtime, adaptar o conceito** | Já existem `confidence` discreta, `seen_in` e `verified`. O decaimento do ECC nem existe em código. Aqui o decaimento vira **proposta** na revisão em lote (nota vencida sugere rebaixar), nunca mudança automática. |
| Teto de injeção, kill switch, ordenar por valor | injeção | **Já temos** | L0/L1 com tetos e arquivo `DISABLED`; nada a fazer. |
| Envelope "HISTORICAL REFERENCE ONLY" | segurança | **Já temos** (variante) | O L1 usa o cabeçalho fixo "dado, não instrução". |
| `/save-session`, `/resume-session`, `ck` (handoff) | continuidade | **Adiar** | A D8 baniu estado transitório no vault. A ideia útil é o campo **"o que NÃO funcionou"**: exigir esse trecho no corpo de notas `trap` e `pattern` destiladas, sem criar arquivo de handoff. |
| `pre-compact` e `session-end` com resumo por LLM | continuidade | **Rejeitar** | Custo de modelo extra, gravação silenciosa a cada Stop, sem scrub de segredos encontrado, e já decidido na D8. |
| Observer de tool calls (`observe.sh`, instincts) | captura | **Rejeitar** | Ratifica a decisão de 2026-09-30; está inativo no nosso perfil. |
| Memory Vault: formato `ecc.memory.v1`, CLI `ecc memory` e MCP | armazenamento e interoperação | **Adaptar (decisão do usuário: híbrido)** | O vault continua sendo a fonte da verdade. Um **adaptador** exporta as notas como espelho somente-leitura em `ecc.memory.v1` (o ECC, quando ligado, as acha por `ecc memory search`) e importa o que o ECC grava (`trust: unreviewed`) para a **fila de candidatos**, nunca direto para o vault. Não depende de `ecc-universal` para funcionar; o CLI do ECC é só um cliente opcional. |
| Busca semântica | recuperação | **Adiar** | Continua dependente do gate da §8 e dos dados do `shadow.jsonl`. |

## 5. S5 — a nossa versão: runtime próprio do second brain (híbrido)

**Decisão do usuário.** Runtime **próprio** para o second brain, com um **adaptador** para o formato do ECC. O vault continua
sendo a fonte da verdade (D11); o ECC vira um cliente opcional.

**O que chamamos de "runtime".** Um ponto de entrada único, local e de vida curta (sem daemon residente), o CLI **`sb`**
(Python da biblioteca padrão, mais `git` e `jq` que já existem), que concentra a lógica hoje espalhada em scripts de bash e
Python. Os hooks passam a ser finos: chamam `sb`. A escolha de **não** ter processo residente é minha: a latência medida
dos hooks (0,18–0,27 s) cabe no teto, e um daemon traria estado, permissões e falhas novas; reavaliar se um índice (FTS5, F4)
exigir. **Nenhum MCP novo nosso** (RFC §1); o agente chama `sb` pelo Bash.

| Subcomando | Função | Reaproveita |
|---|---|---|
| `sb search`, `sb hint` | recuperação L0/L1 e busca manual | `vault_rank.sh`, `session_hint.sh`, `prompt_hint.sh` |
| `sb candidate add|list|prune` | fila de candidatos da sessão (uma linha, 0600, TTL 30 dias com aviso aos 7) | `note_candidates.sh` |
| `sb review capture|promote|stock` | revisão interativa em lote com veredito Save, Improve then Save, Absorb, Drop; `--dry-run` por padrão; **registra a rejeição** | `/learn-eval`, `/promote`, `skill-stocktake` (ideias) |
| `sb sync` | escrita com portão | `vault_sync.py` (guardas existentes + segredos + `verdict`) |
| `sb doctor` | wikilinks quebrados, títulos duplicados, frontmatter ausente, segredos, notas vencidas (somente leitura) | `generate_manifests.py --check/--stale-report` |
| `sb export-ecc`, `sb import-ecc` | adaptador `ecc.memory.v1` (abaixo) | formato do Memory Vault |
| `sb status` | estado e contagens (alimenta a linha de status) | arquivos `<sid>.*` |

**Adaptador `ecc.memory.v1` (hipótese a validar na etapa I0).**
- **Export (vault → ECC), somente leitura.** Artefato derivado, como os manifests: cada nota vira um arquivo Markdown no diretório
  de memória do usuário do ECC, com o frontmatter do esquema (`id`, `title`, `kind`, `scope`, `trust`, `status`, `tags`, `links`,
  `created_at`, `updated_at`). Mapeamento provisório de `type`: `decision`→`decision`; `trap` e `pattern`→`lesson`;
  `concept`→`fact`; `project`→`context`. `trust` é sempre `unreviewed` (o esquema do ECC não tem nível comparável à nossa
  `confidence`; ela segue nos metadados). Notas `scope: project` ficam no escopo de projeto. Regenerado pelo `sb sync`.
- **Import (ECC → vault), sempre via fila.** O que o ECC grava com `ecc memory save` entra como **candidato** em `sb candidate`
  e só vira nota depois do `sb review capture` (veredito, guardas, `confidence: low`). O ECC **nunca** escreve direto no vault.
- **Segurança.** O texto que o ECC lê do espelho continua sendo dado, não instrução (cabeçalho e proveniência preservados); o
  espelho passa pela mesma varredura de segredos; a leitura do ECC não promove nada.
- **O que depende de verificação (NÃO VERIFICADO):** o esquema exato e o validador (`scripts/lib/memory-vault-format.js`), se o
  CLI `ecc memory` funciona só com o plugin ou exige o pacote npm `ecc-universal` (o estudo não achou os binários instalados), e
  onde o ECC procura o diretório de usuário. Instalar `ecc-universal` seria instalar pacote de terceiros: **não será feito sem
  você aprovar o comando**; a etapa I0 verifica lendo o código e usando um diretório de teste.

```
sessão: agente (ou ECC `ecc memory save`) gera candidato ──► fila de candidatos (`sb candidate`, estado local, TTL)
fim da tarefa / sob demanda: `sb review`
   ├─ capture: candidato → veredito → `sb sync` → nota nasce `low`
   ├─ promote: seen_in ≥ 2 → propor Agent-Instruction (y/N), rejeição registrada
   └─ stock:   vencidas, `low` sem confirmação, duplicadas, links quebrados → Keep / Update / Merge / Retire
`sb sync`: guardas atuais + varredura de segredos + `verdict` no log + regenera manifests e o espelho `ecc.memory.v1`
```

**Etapas de implementação (a decidir uma a uma; cada uma do tamanho de um merge, com testes)**

| Etapa | Conteúdo | Pronto quando | Risco |
|---|---|---|---|
| I0 (estudo) | Verificar o adaptador: ler o validador e o formato do Memory Vault, confirmar o diretório e o que exige o CLI; escrever amostras e validá-las num diretório de teste; emendar a nota de decisão de 2026-09-30, o §1 e a D10 do RFC | relatório com o esquema confirmado e decisão sobre depender ou não de `ecc-universal` | baixo (só leitura e fixtures) |
| I1 | Esqueleto do `sb` (`status`, `doctor`, `search`) por cima dos scripts atuais, sem mudar comportamento; varredura de segredos e campo `status`/`supersedes` no schema | testes dos subcomandos; `doctor` acusa link quebrado, título duplicado e segredo falso | baixo |
| I2 | `sb sync` com `verdict` (Save, Improve then Save, Absorb, Drop) e seção "o que NÃO funcionou" no molde de `trap`; hooks de sync passam a chamar o `sb` | `sync.jsonl` registra o veredito | baixo |
| I3 | `sb candidate` (fila com TTL), regra no `AGENTS.md`, contagem na linha de status; **modo sombra** por 2 semanas | fila coleta sem alterar o vault | médio |
| I4 | `sb review capture|promote|stock` interativo, `--dry-run` por padrão, estado retomável, `review.jsonl` com rejeições | ponta a ponta sobre vault de teste e sobre o real em dry-run | médio |
| I5 | Adaptador `sb export-ecc` e `sb import-ecc` (conforme a I0), com teste de ida e volta e de segredos | espelho validado pelo `ecc memory doctor` (se disponível) e import vira candidato | médio |
| I6 | Medição e gate: taxa de aceitação dos candidatos, retrabalho em 60 dias, tempo e tokens da revisão | piso escrito **antes** de medir e aprovado pelo usuário | baixo |

**Métricas e gates (princípio 8).** Hoje não há métrica de qualidade de **escrita**; a I3 e a I6 criam duas: taxa de aceitação de
candidatos (aceitos / propostos) e taxa de retrabalho (notas criadas pela revisão que viram `superseded` ou são descartadas em
60 dias). Todo piso numérico é proposto antes da medição e aprovado pelo usuário. Orçamento de tokens: a fila, a revisão e o
espelho só gastam tokens sob demanda; nada novo entra no contexto por padrão, e o espelho do ECC só pesa quando o ECC está ligado.

**Decisões em aberto para o usuário**
1. **Observer do ECC (`continuous-learning-v2`):** continua rejeitado? Recomendação: sim (log de tool calls sem o porquê, custo
   contínuo, redação de segredos fraca, inativo no perfil `minimal`).
2. **Runtime sem daemon** (CLI `sb` de vida curta) está de acordo? Recomendação: sim, com reavaliação se o índice (F4) pedir.
3. Onde fica a fila de candidatos: `~/.local/state/second-brain/` (recomendado) ou o `00_Inbox` do vault (contraria a D8).
4. Aceita a regra no `AGENTS.md` de que o agente **acrescenta uma linha à fila** quando é corrigido ou descobre uma armadilha?
5. TTL de 30 dias e aviso aos 7 (valores do ECC) ou outros?
6. Ordem: recomendo I0, I1 e I2 primeiro (verificação, valor imediato e risco baixo) e deixar a I3 em sombra antes da I4.
7. Aprova que a I0 leia o código do plugin do ECC e escreva amostras num diretório de teste, **sem** instalar `ecc-universal`?

## Fontes

Plugin `ecc` 2.2.3 em `~/.claude/plugins/cache/ecc/ecc/2.2.3/` (em especial `scripts/hooks/session-start.js`, `session-end.js`,
`commands/learn-eval.md`, `commands/save-session.md`, `skills/continuous-learning-v2/`, `skills/unified-memory/`,
`skills/skill-stocktake/SKILL.md`, `docs/design/ecc-memory-vault.md`, `scripts/instinct-cli.py`); RFC-001, F0 e PRD-002 deste
projeto; `00_META/Frontmatter-Schema.md` e `00_META/skills/second-brain-sync/`.
