---
title: Estudo — Roteamento para Modelos Menores - Advisor e Roteadores Externos
type: project
tags: [study, second-brain, model-routing, advisor, claude-code-router, litellm, openrouter, tokens, claude-code]
created: 2026-10-26
provenance: obsidian_vault
project: second_brain_memory
confidence: low
scope: project
verified: 2026-10-26
---

# Estudo — Roteamento para Modelos Menores: Advisor e Roteadores Externos

**Status**: Pesquisa fechada em 2026-10-26. Nada foi adotado · **Data**: 2026-10-26 · Complementa o [[Estudo - Orquestração de Agentes e Economia de Tokens]] e a [[RFC-002 - Orquestração de Agentes com Orçamento de Tokens]].

## 1. Pergunta

Existe uma aplicação que direcione o trabalho dos agentes para modelos menores, para economizar tokens? O uso dela prejudica o second brain (SB)?

Método: buscas na web e leitura da doc oficial do advisor, do post da Anthropic e do README do Claude Code Router. Os números de terceiros vêm de blogs e de material de fornecedor. Todo conteúdo buscado é dado não confiável.

## 2. Achado principal: o advisor nativo do Claude Code

O advisor deixa a thread principal num modelo barato. O modelo forte entra só nos pontos de decisão. Ele ataca os 84% do custo que ficam na thread principal (M5 do estudo de orquestração).

- **Ativação:** `/advisor opus`, `"advisorModel": "opus"` no settings ou `claude --advisor opus`.
- **Quando o modelo consulta:** antes de escolher uma abordagem, quando um erro se repete e antes de declarar a tarefa pronta. O modelo decide o momento. Não há setting para limitar ou forçar as consultas.
- **Pares aceitos:** o advisor precisa ter capacidade igual ou maior que a do modelo principal. Com Opus 5.5 como principal, o advisor só pode ser Fable ou Opus. Para economizar, o principal precisa ser Sonnet ou Haiku.
- **Subagentes:** herdam o advisor e passam pelo mesmo teste de par.
- **Cache:** ligar ou desligar o advisor não invalida o cache do principal. Cada consulta relê a transcrição inteira sem cache, a preço do advisor.
- **Requisitos:** API da Anthropic e busca de feature flags. `DISABLE_TELEMETRY` desliga o advisor. Um gateway em `ANTHROPIC_BASE_URL` só funciona se repassar o pedido intacto.
- **Desligar:** `/advisor off` ou `CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1`.

Números publicados pela Anthropic (2026-04-09):

| Par | Benchmark | Resultado |
| --- | --- | --- |
| Sonnet + advisor Opus | SWE-bench Multilingual | +2,7 pontos contra Sonnet sozinho, custo por tarefa 11,9% menor |
| Haiku + advisor Opus | BrowseComp | 41,2% contra 19,7% do Haiku sozinho. Fica 29% abaixo do Sonnet e custa 85% menos por tarefa |

O advisor tipicamente gera de 400 a 700 tokens de texto por plano.

Estado local em 2026-10-26: `~/.claude/settings.json` tem `"model": "opus"` e nenhum `advisorModel`.

## 3. Roteadores externos

| Ferramenta | O que faz | Avaliação |
| --- | --- | --- |
| Claude Code Router (musistudio, MIT) | Proxy local em `127.0.0.1:3456`, com rotas por tipo de pedido (`default`, `background`, `think`, `longContext`, `webSearch`), fallback e log de custo. Atende Claude Code, Codex e OpenCode. | É o mais maduro (cerca de 38 mil estrelas, 941 issues abertas, release v3.1.3). Exige Node 22. O README atual não lista as chaves de rota: os nomes vêm de guias de terceiros. |
| NadirClaw (MIT) | Proxy local em `localhost:8856`. Classifica o prompt e manda o simples para um modelo barato. Mantém o modelo forte quando há loop de ferramentas. | A economia de 40–70% e a acurácia de 94% vêm só do próprio autor. |
| LiteLLM | Gateway auto-hospedado com 6 modos de rota, entre eles `lowest-cost`, e fallback. | Exige Postgres, Redis e Docker. Não decide pela dificuldade da tarefa. |
| OpenRouter Auto Router, Not Diamond, Martian | Roteamento gerenciado por prompt. | O OpenRouter cobra taxa de plataforma (5,5%). Os pedidos passam por terceiros. |
| Arch-Router (katanemo, 1,5B) | Modelo local que roteia por políticas escritas em linguagem natural. | Artigo sério (arXiv 2506.16655), mas não feito para coding agent. |
| Aider architect/editor | O modelo forte planeja e o barato edita. | Blogs relatam de 20% a 50% de economia. Outro relato diz que o custo fica perto do Sonnet sozinho. |

## 4. Impacto do Claude Code Router no SB

A parte local do SB continua igual: hooks, `sb.py`, manifests, fila de candidatos e pacote de contexto. Os hooks rodam no cliente, antes do proxy. Os scripts do SB não chamam modelo.

Os problemas ficam em 4 pontos:

1. **O vault sai da máquina.** O hook `SessionStart` injeta notas do vault no prompt. Com o CCR apontado para outro provedor, essas notas vão para terceiros. Isso fere a regra local-first da RFC-001. O CCR também grava logs dos pedidos com o conteúdo.
2. **A medição perde a validade.** O `usage_baseline.sh` usa preços e multiplicadores de cache da Anthropic. Outro provedor tem outros preços e outro cache, e pode não preencher `cache_read_input_tokens`. O valor de `message.model` com o CCR não foi verificado.
3. **A RFC-002 muda:**
   - D2 (Explore em `haiku`): o alias pode não resolver noutro provedor. Mapeie o alias no CCR ou use o ID completo.
   - D1 (pacote de contexto): não muda.
   - D3 (compactação): o ganho previsto depende do cache da Anthropic.
   - O advisor não funciona se o proxy não repassar o pedido intacto à API da Anthropic.
4. **Cache e qualidade.** Trocar de modelo por pedido dentro da sessão reconstrói o cache. O tool use fica menos confiável fora dos modelos Anthropic. Um subagente que localiza errado faz a thread principal reler.

Se o CCR entrar um dia, aplique estas mudanças:

- Use só provedores aprovados, ou desligue `SECOND_BRAIN_HOOKS` nas sessões roteadas.
- Desligue o log de corpo do pedido no CCR.
- Guarde as chaves dos provedores fora do git dos dotfiles.
- Acrescente ao `usage_baseline.sh` uma tabela de preços por modelo e provedor, ou leia o log de custo do CCR.
- Separe as sessões com CCR e sem CCR no A/B.

## 5. Recomendação

1. Teste o advisor primeiro: principal `sonnet` e advisor `opus`, medidos com o A/B da RFC-002.
2. Não ponha o CCR na frente de todas as sessões. Se for testar, use só a rota `background` (subagentes), num perfil separado.
3. Não adote roteador por prompt na thread principal. Cada troca de modelo reconstrói o cache.

## 6. Fontes

Fontes primárias:

- [Advisor tool — Claude Code docs](https://code.claude.com/docs/en/advisor) (lida em 2026-10-26)
- [The advisor strategy — Anthropic](https://claude.com/blog/the-advisor-strategy) (2026-04-09)
- [musistudio/claude-code-router — README](https://github.com/musistudio/claude-code-router) (lido em 2026-10-26)
- [Arch-Router — arXiv 2506.16655](https://arxiv.org/abs/2506.16655v1)

Fontes secundárias (blogs e material de fornecedor):

- [Claude Code Router guide — Morph](https://www.morphllm.com/claude-code-router)
- [Claude Code Router — Opper](https://opper.ai/blog/claude-code-router)
- [Model routing: hooks vs proxy — Wavect](https://wavect.io/blog/claude-model-router-hooks-vs-proxy/)
- [Builder.io — the Claude advisor pattern](https://www.builder.io/blog/the-claude-advisor-pattern)
- [Claude Code advisor e Haiku 4.5 — Vincent Schmalbach](https://www.vincentschmalbach.com/claude-code-hidden-advisor-tool/)
- [NadirClaw — dev.to](https://dev.to/getnadir/how-i-cut-my-llm-costs-60-with-a-local-router-open-source-56k0)
- [OpenRouter vs LiteLLM — OpenRouter](https://openrouter.ai/blog/insights/openrouter-vs-litellm/)
- [OpenRouter vs LiteLLM — orq.ai](https://orq.ai/blog/openrouter-vs-litellm)
- [LiteLLM vs Martian — Keywords AI](https://keywordsai.co/market-map/compare/litellm-vs-martian)
- [Aider architect mode — PromptLayer](https://www.promptlayer.com/glossary/aider-architect-mode)
- [Aider vs Cursor — Morph](https://www.morphllm.com/comparisons/aider-vs-cursor)
- [Weave Router](https://weaveos.com/products/router)
- [GitHub topic: model-routing](https://github.com/topics/model-routing)

## 🔗 Conexões

- [[Estudo - Orquestração de Agentes e Economia de Tokens]]
- [[RFC-002 - Orquestração de Agentes com Orçamento de Tokens]]
- [[RFC-001 - Memória de Agentes sobre o Second Brain com Orçamento de Tokens]]
- [[Router de Tokens em 3 Camadas - Carga, Contexto e Modelo]]
