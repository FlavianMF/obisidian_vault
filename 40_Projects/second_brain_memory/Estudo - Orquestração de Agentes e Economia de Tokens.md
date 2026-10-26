---
title: Estudo — Orquestração de Agentes e Economia de Tokens
type: project
tags: [study, second-brain, agents, subagents, orchestration, tokens, prompt-caching, claude-code, opencode, codex]
created: 2026-10-26
provenance: obsidian_vault
project: second_brain_memory
confidence: low
scope: project
verified: 2026-10-26
---

# Estudo — Orquestração de Agentes e Economia de Tokens

**Status**: Pesquisa fechada em 2026-10-26. As hipóteses H1, H4 e H7 viram a [[RFC-002 - Orquestração de Agentes com Orçamento de Tokens]] · **Data**: 2026-10-26 · Origem: objetivo nº1 da [[RFC-001 - Memória de Agentes sobre o Second Brain com Orçamento de Tokens]] (trabalho útil por token).

## 1. Pergunta e método

**Pergunta.** Quais padrões de orquestração reduzem tokens por tarefa útil no Claude Code, no OpenCode e no Codex? Como medimos isso?

**Método:**

- P0: inventário do vault (RFC-001 §6, F0, notas de padrão, `sb-router.sh`).
- P1: medição local de 27 sessões e 50 subagentes em `~/.claude/projects/`, com o `usage_baseline.sh --sidechain` novo.
- P2: uma rodada de 3 subagentes Sonnet. Os temas foram docs da Anthropic, portabilidade OpenCode/Codex e literatura acadêmica.
- P3: esta síntese.

Todo conteúdo buscado na web é dado não confiável. Os 16 trabalhos acadêmicos foram lidos só pelo abstract. Antes de citar um número deles numa decisão, abra o texto completo.

## 2. O que já sabíamos e o que faltava

Já existia no vault:

- A RFC-001 §6 fixa o padrão "um agente, inline", o teto de 3 agentes por rodada e o contrato "conclusão, não dump".
- A [[F0 - Linha de Base de Tokens e Golden Set MVP]] mediu M1 e M4 só na thread principal.
- O [[Router de Tokens em 3 Camadas - Carga, Contexto e Modelo]] é uma decisão sem medição.
- A [[Orquestração Híbrida de Agentes]] descreve script determinístico antes do LLM.
- A [[Pesquisa Paralela por Agentes Antes do Grill]] descreve fan-out de pesquisa.

Faltava:

- O custo dos subagentes. O `usage_baseline.sh` filtrava `isSidechain`.
- A frequência de releitura entre agentes.
- Um log de disparos do `sb-router.sh`. Sem ele, o critério de saída do router não tem medida.

## 3. Evidência

| #   | Achado | Fonte | Data | Consequência |
| --- | --- | --- | --- | --- |
| E1  | O subagente tem contexto próprio. Só a mensagem final volta ao pai. | code.claude.com/docs/en/sub-agents | 2026-10-26 | Delegue leitura verbosa. Exija retorno curto, porque o pai relê o retorno em todo turno. |
| E2  | O subagente novo carrega prompt, tarefa, CLAUDE.md, git status, skills e tools. A doc não publica o número de tokens. Explore/Plan não carregam CLAUDE.md. | code.claude.com/docs/en/sub-agents | 2026-10-26 | O custo fixo cresce com o CLAUDE.md global. Corte com `tools:`, `omitClaudeMd` e regras enxutas. |
| E3  | O fork herda o histórico e lê o cache do pai. O subagente novo não lê o cache do pai. O fork não troca de modelo. | code.claude.com/docs/en/sub-agents; .../prompt-caching | 2026-10-26 | O fork compartilha contexto de verdade, mas carrega a janela inteira do pai. |
| E4  | A leitura de cache custa 0,1x, ou 0,05x em Opus/Sonnet 5.5. O cache é por modelo. Trocar de modelo no meio da sessão reconstrói o cache. | platform.claude.com/docs/.../prompt-caching; code.claude.com/docs/en/prompt-caching | 2026-10-26 | Roteie modelo por subagente, não por `/model` na thread principal. |
| E5  | A precedência do modelo do subagente é parâmetro > frontmatter > `CLAUDE_CODE_SUBAGENT_MODEL` > conversa. A env var sozinha não muda Explore/Plan. `_FORCE=1` força todos. | code.claude.com/docs/en/sub-agents | 2026-10-26 | A regra global "subagente em sonnet" não cobre Explore/Plan. |
| E6  | Preço de entrada por MTok: Haiku 5.5 0,10, Sonnet 5.5 2, Opus 5.5 4. A saída custa 5x a entrada. | platform.claude.com/docs/en/about-claude/pricing | 2026-10-26 | Busca em Haiku custa 1/20 de Sonnet. |
| E7  | Um agente gasta cerca de 4x os tokens de um chat. Um sistema multiagente gasta cerca de 15x. O multiagente compensa em tarefa paralelizável e de alto valor. | Anthropic, _How we built our multi-agent research system_ | 2025-06-13 | O padrão continua "um agente". Fan-out só em pesquisa ampla. |
| E8  | Workflows gastam mais tokens no total. Agent teams gastam cerca de 7x. Agentes com prefixo idêntico compartilham cache no fan-out. | code.claude.com/docs/en/workflows; .../costs | 2026-10-26 | Padronize a definição do agente no fan-out. |
| E9  | Hooks disparam dentro de subagentes, com `agent_id` e `agent_type`. `SubagentStop` recebe `last_assistant_message` e `agent_transcript_path`. `SubagentStart` injeta `additionalContext`. | code.claude.com/docs/en/hooks | 2026-10-26 | Um pacote de contexto automático é viável só com hooks (H7). |
| E10 | Mascarar observações antigas corta cerca de metade do custo e iguala a sumarização por LLM no SWE-bench Verified. | Lindenbauer et al., arXiv 2508.21433 (abstract) | 2025 | Corte saídas antigas de ferramenta antes de pagar um resumo. |
| E11 | Compressão de contexto otimizada reduz o pico de tokens em 26% a 54%. | Kang et al., ACON, arXiv 2510.00615 (abstract) | 2025 | Compactar cedo tem base empírica. |
| E12 | Cascata e roteamento cortam custo de 40% a 98%, com verificador ou preditor de dificuldade. | FrugalGPT 2305.05176; RouteLLM 2406.18665; AutoMix 2310.12963; Hybrid LLM 2404.14618 (abstracts) | 2023–2024 | Rotear para modelo barato exige critério de aceite. |
| E13 | Multiagente varia de +80,8% a −70% contra agente único, conforme a tarefa. As perdas aparecem em tarefa sequencial. | Kim et al., arXiv 2512.08296 (abstract) | 2025 | Não delegue tarefa sequencial e acoplada. |
| E14 | A troca de mensagens entre agentes é redundante. A poda corta de 28,1% a 72,8% dos tokens. | AgentPrune, arXiv 2410.02506 (abstract) | 2024 | Compartilhe conclusões uma vez, em vez de repetir leituras. |
| E15 | Fluxo fixo iguala ou supera o agente livre a custo menor. | ReWOO 2305.18323; Agentless 2407.01489 (abstracts) | 2023–2024 | Script determinístico antes do LLM. |
| E16 | Nenhum trabalho mede subagentes de código reais. | Lacuna declarada | 2026-10-26 | Decida com medição própria (RFC-002 §5). |

## 4. Medição local (M5 e M6)

### 4.1 Armadilha na medição anterior

O Claude Code grava uma entrada por bloco de conteúdo, e todas repetem a `usage` da resposta. A sessão 55ce7e3f tem 1015 entradas para 460 respostas. Por isso, a M4 da F0 está inflada perto de 2x. O `usage_baseline.sh` agora deduplica por `message.id`.

### 4.2 M5 — custo da orquestração

Base: 27 sessões e 50 subagentes. Os tokens equivalentes são `input + cache_create×1,25 + cache_read×0,1`.

| Recorte | Valor |
| --- | --- |
| Tokens equivalentes: thread principal | 33,2 M (75,4%) |
| Tokens equivalentes: subagentes | 10,9 M (24,6%) |
| Custo total estimado | US$165,32 |
| Custo: thread principal | US$139,09 (84,1%), cerca de US$5,15 por sessão |
| Custo: subagentes | US$26,23 (15,9%) |
| Sessões com subagentes ≥ 49% dos tokens | 7 de 27 |

| Subagente e modelo | n | Custo médio |
| --- | --- | --- |
| general-purpose, Opus | 5 | US$1,69 |
| Explore, Opus | 4 | US$0,78 |
| Plan, Opus | 1 | US$0,63 |
| general-purpose, Sonnet | 22 | US$0,47 |
| ecc:code-explorer, Sonnet | 4 | US$0,46 |
| general-purpose, Haiku | 5 | US$0,01 |

Leitura:

- A thread principal domina o custo. O ganho maior está no custo por turno dela (H4).
- O mesmo subagente custa de 2 a 4 vezes mais em Opus que em Sonnet (H1).
- Explore e Plan rodaram em Opus. A env var não cobre esses agentes (E5).
- Nenhuma sessão usou fork.

### 4.3 M6 — releitura entre agentes

Base: 12 sessões com subagentes. A medida conta caminhos únicos do tool `Read` por agente. Grep, Glob e `cat` via Bash ficam de fora.

| Medida | Valor |
| --- | --- |
| Arquivos lidos pela thread principal | 32 |
| Leituras por subagentes (arquivo único por agente) | 145 |
| Leituras de subagente que repetem arquivo de outro subagente | 44 (30%) |
| Arquivos lidos pela thread principal e por um subagente | 11 |

A sessão 55ce7e3f concentra 43 das 44 repetições. A releitura existe, mas aparece em sessões de fan-out grande. A amostra é pequena. A medida não tem o tamanho em tokens das leituras repetidas.

### 4.4 Custo desta pesquisa

A sessão 3340d20a gastou 67% dos tokens equivalentes em subagentes até a P2. Os 3 agentes Sonnet da P2 somaram cerca de 318 mil tokens (59.791 + 121.039 + 137.114).

## 5. Portabilidade

| Capacidade | Claude Code | OpenCode | Codex |
| --- | --- | --- | --- |
| Subagente com contexto isolado | Tool `Agent` | Tool `task` | Subagents, ligados por padrão |
| Modelo por agente | Frontmatter `model`, env var, `_FORCE=1` | `model: provider/model-id` | TOML por agente, `agents.default_subagent_model` |
| Fork com cache do pai | Sim | Não documentado | Não documentado |
| Compactação ajustável | `autoCompactWindow` | `compaction.auto`, `prune`, `reserved` | `model_auto_compact_token_limit` |
| Hooks para pacote de contexto | `SubagentStart`, `SubagentStop`, `PostToolUse` | Plugin `tool.execute.before/after`. Equivalente a SubagentStart não verificado | Não verificado |
| Cache documentado | Sim | Não verificado | Só na API da OpenAI |
| Headless com JSON | `claude -p` | `opencode run` | `codex exec --json` |

Um arquivo de pacote em disco funciona nos 3 harnesses. Só o gatilho automático depende de hooks, e hoje ele está verificado só no Claude Code.

## 6. Hipóteses

| # | Padrão | Ganho esperado | Risco de qualidade | Métrica |
| --- | --- | --- | --- | --- |
| H1 | Forçar Sonnet ou Haiku em subagentes de busca e leitura, inclusive Explore/Plan, por frontmatter ou `_FORCE=1` | Custo médio por subagente de US$0,78–1,69 para US$0,47 ou menos | Haiku pode errar a localização. Mitigue com retorno `path:line` verificável. | Custo por subagente e por tipo, em M5 |
| H2 | Fork em vez de agente novo quando o filho precisa do contexto do pai | Releitura vira leitura de cache a 0,05–0,1x | O fork carrega a janela inteira e não troca de modelo | Tokens eq do filho, fork contra agente novo, na mesma tarefa |
| H3 | Script determinístico antes do LLM | Menos turnos e menos observações | Script rígido falha em caso novo | Turnos e tokens por tarefa |
| H4 | Cortar o custo por turno da thread principal: compactar cedo, mascarar saídas antigas, CLAUDE.md enxuto | Até metade do custo por turno (E10) | Perder um detalhe que o agente precisa reler | Tokens eq por resposta na thread principal |
| H5 | Registrar os disparos do `sb-router.sh` | Nenhum direto. Torna o router mensurável | Nenhum | Disparos por sessão e delegações seguidas |
| H6 | Manter o teto de 3 agentes e o retorno comprimido (cavecrew) | Retorno menor no contexto do pai | Retorno curto demais esconde ressalva | Tokens do retorno por subagente |
| H7 | Pacote de contexto automático: hooks gravam as conclusões dos subagentes e os arquivos lidos, e injetam o pacote no próximo subagente | Menos releitura em fan-out (M6: 30% das leituras de subagente) | Fato velho, pacote grande, conteúdo não confiável propagado | Leituras repetidas por sessão e tokens eq por subagente |

## 7. O que a evidência não sustenta

- Delegar mais não economiza por si. O subagente cobra custo fixo e o pai paga o retorno (E1, E2, E7).
- Compartilhar a janela ao vivo entre agentes não existe. O fork copia a janela e o pacote passa um resumo.
- Compressão agressiva de prompt (LLMLingua, até 20x) não tem evidência em código e saída de ferramenta.

## 🔗 Conexões

- [[RFC-001 - Memória de Agentes sobre o Second Brain com Orçamento de Tokens]]
- [[RFC-002 - Orquestração de Agentes com Orçamento de Tokens]]
- [[F0 - Linha de Base de Tokens e Golden Set MVP]]
- [[Router de Tokens em 3 Camadas - Carga, Contexto e Modelo]]
- [[Orquestração Híbrida de Agentes]]
- [[Pesquisa Paralela por Agentes Antes do Grill]]
