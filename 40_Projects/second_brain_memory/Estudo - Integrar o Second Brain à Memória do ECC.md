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
| Observer de tool calls (`observe.sh`, instincts) | captura | **Adotar como fonte de captura (decisão do usuário, 2026-10-15)** | O usuário ligou o perfil completo e o observer; a rejeição de 2026-09-30 foi revertida (ver [[Reavaliação - ECC com Perfil Completo e Observer Ligado]]). Os instincts **nunca** viram nota sozinhos: entram na fila de candidatos, recebem veredito na revisão e passam pelas guardas do `vault_sync.py`. |
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
| I0 (estudo) | Verificar o adaptador: ler o validador e o formato do Memory Vault, confirmar o diretório e o que exige o CLI; escrever amostras e validá-las num diretório de teste; **testar o redator de segredos do `observe.sh` com credenciais falsas e conferir as permissões dos arquivos do observer, num `CLV2_HOMUNCULUS_DIR` temporário; confirmar o nome e o efeito do limite de injeção de instincts (`ECC_MAX_INJECTED_INSTINCTS`)**; ler o formato dos instincts (`instincts/personal|pending`) para o importador. A emenda da nota de decisão de 2026-09-30, do §1 e da D10 do RFC já foi feita em 2026-10-15 | relatório com o esquema confirmado, o resultado do teste do redator e decisão sobre depender ou não de `ecc-universal` | baixo (só leitura e fixtures) |
| I1 (entregue em 2026-10-15) | Esqueleto do `sb` (`status`, `doctor`, `search`) por cima dos scripts atuais, sem mudar comportamento; varredura de segredos e campo `status`/`supersedes` no schema | testes dos subcomandos; `doctor` acusa link quebrado, título duplicado e segredo falso | baixo |
| I2 (entregue em 2026-10-15; o hook do dotfiles aguarda merge) | `sb sync` com `verdict` (Save, Improve then Save, Absorb, Drop) e seção "o que NÃO funcionou" no molde de `trap`; hooks de sync passam a chamar o `sb` | `sync.jsonl` registra o veredito | baixo |
| I3 (entregue em 2026-10-15; sombra de 2026-10-15 a 2026-10-29; falta a rotina de retenção do homunculus, que espera existir `observations.jsonl`) | `sb candidate` (fila com TTL), regra no `AGENTS.md`, contagem na linha de status; **modo sombra** por 2 semanas | fila coleta sem alterar o vault | médio |
| I4 (entregue em 2026-10-22) | `sb review capture|promote|stock` interativo, `--dry-run` por padrão, estado retomável, `review.jsonl` com rejeições | ponta a ponta sobre vault de teste e sobre o real em dry-run | médio |
| I5 | Adaptador `sb export-ecc` e `sb import-ecc` (conforme a I0), com teste de ida e volta e de segredos | espelho validado pelo `ecc memory doctor` (se disponível) e import vira candidato | médio |
| I6 | Medição e gate: taxa de aceitação dos candidatos, retrabalho em 60 dias, tempo e tokens da revisão | piso escrito **antes** de medir e aprovado pelo usuário | baixo |

**Métricas e gates (princípio 8).** Hoje não há métrica de qualidade de **escrita**; a I3 e a I6 criam duas: taxa de aceitação de
candidatos (aceitos / propostos) e taxa de retrabalho (notas criadas pela revisão que viram `superseded` ou são descartadas em
60 dias). Todo piso numérico é proposto antes da medição e aprovado pelo usuário. Orçamento de tokens: a fila, a revisão e o
espelho só gastam tokens sob demanda; nada novo entra no contexto por padrão, e o espelho do ECC só pesa quando o ECC está ligado.

**Decisões em aberto para o usuário**
1. **Observer do ECC (`continuous-learning-v2`):** **resolvida em 2026-10-15.** O usuário escolheu o perfil completo com o observer
   ligado; a recomendação anterior (manter rejeitado) foi superada. As questões que sobraram (limite temporário de injeção,
   retenção, projetos excluídos, teste do redator de segredos) estão em
   [[Reavaliação - ECC com Perfil Completo e Observer Ligado]]. O importador `sb import-ecc` passa a ler também os instincts
   (`instincts/personal|pending`), não só o `ecc.memory.v1`.
2. **Runtime sem daemon** (CLI `sb` de vida curta): **aprovado em 2026-10-15**, com reavaliação se o índice (F4) pedir.
3. Local da fila de candidatos: **aprovado `~/.local/state/second-brain/`** (a alternativa, o `00_Inbox` do vault, contraria a D8).
4. Regra no `AGENTS.md` de que o agente **acrescenta uma linha à fila** quando é corrigido ou descobre uma armadilha:
   **aprovada**. A linha só entra no `AGENTS.md` junto com a I3, quando o `sb candidate` existir; antes disso ela citaria um
   comando inexistente. Permanece válido que o agente **não** roda `/promote`, `/evolve`, `/instinct-import` nem `/prune` por conta
   própria (o `sb review` pode invocá-los só em `--dry-run`).
5. TTL de 30 dias e aviso aos 7: **aprovado**. Para observações e instincts `pending` do ECC, o `sb` implementa a rotina própria
   (resultado da I0, item 3).
6. Ordem: **aprovada**. I1 e I2 primeiro (verificação feita na I0; valor imediato, risco baixo); a I3 roda em **sombra por 2
   semanas** antes de a I4 existir. A I5 de exportação fica **adiada** (resultado da I0) e só o import de instincts segue.
7. Aprova que a I0 leia o código do plugin do ECC e escreva amostras num diretório de teste, **sem** instalar `ecc-universal`?
   **Resolvida em 2026-10-15:** a I0 rodou assim. Resultado na próxima seção.

## Resultado da I0 (2026-10-15)

A I0 leu o código do plugin `ecc` 2.2.3 e rodou o `observe.sh`, o `session-start.js` e o `memory.js` reais em diretórios
temporários (`CLV2_HOMUNCULUS_DIR`, `ECC_MEMORY_USER_ROOT`, `HOME` e `CLV2_CONFIG` isolados, observer desligado). Nada foi
instalado e nada tocou `~/.local/share/ecc-homunculus` nem `~/.ecc`. Os scripts de teste ficam no scratchpad da sessão.

**1. Limite de injeção de instincts: o nome combinado não funciona.**
`ECC_MAX_INJECTED_INSTINCTS=0` **não desliga** a injeção: o código exige inteiro maior que zero e, para `0`, volta ao padrão 6
(`getMaxInjectedInstincts`, `session-start.js`). Testado: com `0` o instinct de confiança 0,9 continua entrando. O que funciona:

| Variável | Efeito testado |
|---|---|
| `ECC_INSTINCT_CONFIDENCE_THRESHOLD=1` (ou `0.95`) | nenhum instinct injetado; a confiança máxima documentada do ECC é 0,9 |
| `ECC_MAX_INJECTED_INSTINCTS=1` | injeta no máximo 1 |
| `ECC_SESSION_START_CONTEXT=off` | desliga toda a injeção do SessionStart (instincts, learned skills, resumo da sessão anterior) |

Para a decisão 1 da Reavaliação (bloquear a injeção por 2 semanas), a variável correta é
`ECC_INSTINCT_CONFIDENCE_THRESHOLD=1`: bloqueia só os instincts e mantém o resto. O hook lê só `instincts/personal` e
`instincts/inherited`; `pending` nunca é injetado. Hoje há 3 instincts do projeto `obsidian_vault`, todos com confiança 0,5, abaixo
do limiar padrão de 0,7, então ainda nada seria injetado de qualquer forma.

**2. Redator de segredos do `observe.sh`: fraco, como o registro de 2026-09-30 dizia.**
Com 11 credenciais **falsas**, passadas como entrada (`tool_start`) e saída (`tool_complete`) de um Bash:

| Resultado | Casos |
|---|---|
| Redigido | `API_KEY=...`, `Authorization: Bearer ...`, `password: '...'` longa |
| **Vaza** | senha curta (`DB_PASSWORD=hunter2`, menos de 8 caracteres), PAT do GitHub sem palavra-chave, `aws_secret_access_key=...` (o `_` após `secret` quebra o padrão), id de chave AWS, JWT, URL com credencial (`postgres://user:senha@host`), chave privada PEM, token do Slack | <!-- sb-allow-secret: exemplo fictício -->

A regex só casa quando uma palavra-chave (`api_key`, `token`, `secret`, `password`, `authorization`, `credential`, `auth`) precede o
valor, seguida de até 8 separadores. O filtro `ECC_OBSERVE_SKIP_PATHS` funciona (um `cwd` contendo `secrets` não gera registro), mas
casa por substring só contra o `cwd` da sessão, não contra os arquivos que as tools tocam. Permissões: o log fica em
`0664` e os diretórios em `0775` (efeito do `umask 002`); só `project.json` e `projects.json` são `0600`. Se as transcrições do
Claude Code já guardam o mesmo conteúdo sem redação, o log do observer só acrescenta uma cópia (NÃO VERIFICADO).
Consequências: a varredura de segredos do `sb` antes de importar um instinct precisa ser **própria e mais ampla** que a do
observer, e a raiz `~/.local/share/ecc-homunculus` deve ficar em `0700`.

**3. Retenção: o ECC não implementa o TTL de 30 dias que a decisão 3 aprovou.**
O purge do `observe.sh` só apaga `observations-*.jsonl` (arquivos rotacionados) com mais de 30 dias. O `observations.jsonl` ativo
só rotaciona ao atingir 10 MB. Cumprir o TTL de 30 dias para observações e instincts `pending` exige rotina própria do `sb`
(somente sobre arquivos do homunculus, com `--dry-run` por padrão).

**4. Formato dos instincts (para o importador).**
Arquivo `.md` ou `.yaml` com um ou mais blocos de frontmatter (`---`): `id`, `trigger`, `confidence` (0,3 a 0,9), `domain`,
`source` (ex.: `session-observation`), `scope`, `project_id`, `project_name`; corpo com `## Action` (a linha injetada) e
`## Evidence` (contagem, id da sessão, padrão observado). Está em `instincts/personal|pending|inherited` por projeto, em
`projects/<hash>/`. O importador lê frontmatter e `## Action`/`## Evidence` e **trata o `## Evidence` como dado não confiável**:
ele cita o id da sessão e descreve ações do agente.

**5. Adaptador `ecc.memory.v1`: validado, com ressalvas que reduzem o valor da I5.**
- Esquema confirmado em `scripts/lib/memory-vault-format.js`: `kind` ∈ `context`, `decision`, `fact`, `handoff`, `lesson`,
  `note`, `preference`, `runbook`; `scope` ∈ `project`, `team`, `user`; `trust` só `unreviewed`; `status` ∈ `active`, `rejected`,
  `superseded`; id `mem_<minúsculas>`; corpo até 64 KiB. O mapeamento provisório do §anterior cabe no esquema.
- O CLI roda **sem `ecc-universal`**: `node <installPath>/scripts/memory.js init|save|search|read|doctor`, só com módulos do
  próprio Node. O diretório de usuário é `~/.ecc/memory` (`ECC_MEMORY_USER_ROOT` sobrescreve); layout
  `<raiz>/<kind no plural>/<id>.md`, arquivos `0600`, subdiretórios `0700`.
- A escrita é **somente criação**: salvar o mesmo id duas vezes falha. Um exportador que atualiza notas precisa remover e recriar o
  arquivo do espelho (ele é derivado) ou marcar `status: superseded`.
- `--link` e `links` aceitam só ids `mem_*`, não wikilinks; o exportador mapeia wikilink para id ou os mantém no corpo.
- A varredura de segredos do ECC cobre chave de provedor, Stripe, npm, Hugging Face, GitHub, Google, Slack, AWS e chave privada, mas
  **não** JWT, URL com credencial nem senha curta (testado: um corpo com JWT foi aceito).
- `doctor` e `search` funcionam e acusam ids duplicados, links quebrados e arquivos inválidos.
- **Nenhum hook injeta o Memory Vault.** Só o CLI e o MCP opt-in (`ecc-memory-mcp`) o leem; o `unified-memory` não roda sozinho.
  O espelho só serve se um agente do ECC chamar `ecc memory search` ou se o MCP for habilitado.

**6. `doc-file-warning` não bloqueia.** O hook sai sempre com código 0 e só avisa (`scripts/hooks/doc-file-warning.js`). O registro de
2026-09-30 sobre bloqueio de escrita de `.md` não vale para a 2.2.3; o que interrompe é o GateGuard. Nota corrigida abaixo.

**Decisões que a I0 deixa para o usuário**
- **Depender de `ecc-universal`?** Recomendação: **não**. Nada do que o `sb` precisa exige o pacote. O exportador escreve os
  arquivos no formato e usa `node <installPath>/scripts/memory.js doctor` só como validação opcional nos testes.
- **I5 (exportar o vault para o Memory Vault do ECC):** recomendação de **adiar**. Como nenhum hook lê o espelho, o custo de manter
  um espelho derivado não se paga enquanto não houver MCP ou chamada do CLI. Manter só o **import** de instincts, que é a fonte
  de captura. Reabrir se o uso do `ecc memory search` ou do MCP aparecer.
- **Aplicar `ECC_INSTINCT_CONFIDENCE_THRESHOLD=1`** em `claude/settings.json` até 2026-10-29, em lugar do
  `ECC_MAX_INJECTED_INSTINCTS=0`, e `chmod 700` na raiz do homunculus (acrescentar ao alvo `make ecc-observer-config`).
- **Rotina própria de retenção** (TTL de 30 dias) no `sb`, na I3, com `--dry-run` por padrão.

## Fontes

Plugin `ecc` 2.2.3 em `~/.claude/plugins/cache/ecc/ecc/2.2.3/` (em especial `scripts/hooks/session-start.js`, `session-end.js`,
`commands/learn-eval.md`, `commands/save-session.md`, `skills/continuous-learning-v2/`, `skills/unified-memory/`,
`skills/skill-stocktake/SKILL.md`, `docs/design/ecc-memory-vault.md`, `scripts/instinct-cli.py`); RFC-001, F0 e PRD-002 deste
projeto; `00_META/Frontmatter-Schema.md` e `00_META/skills/second-brain-sync/`.
