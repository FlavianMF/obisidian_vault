---
title: Pesquisa: Claude Code (anthropics/claude-code) — Arquitetura do Harness
type: moc
tags: [moc, claude-code, ai-agent, harness, agent-architecture]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

# Pesquisa: Claude Code (anthropics/claude-code) — arquitetura do harness

> Repositório: [github.com/anthropics/claude-code](https://github.com/anthropics/claude-code) ·
> Docs: [code.claude.com/docs](https://code.claude.com/docs/en/overview) ·
> Licença: **proprietária** (© Anthropic PBC, Commercial ToS)
>
> Pesquisa de 2026-09-16/17, com o repo pinado em
> `68ac8bbf0245b615b41517bf8f2b2f35af1ae31d` e a instalação local `2.1.274`.

## Por que essa pesquisa

Segundo caso de estudo de harness de agentes deste projeto, depois de
[`opencode`](../opencode/00_indice.md). O objetivo é o mesmo: extrair padrões arquiteturais
para o harness próprio de orquestração LLM ↔ Capella
(`notes/arquitetura_hibrida_mcp_capella.md`, `notes/metodologia_dev_mcp.md`).

O Claude Code é o caso mais relevante porque é o harness de codificação mais usado em
produção hoje, e porque — apesar de ser software fechado — ele **publica o contrato inteiro
da sua arquitetura de extensão**: 407 KB de declarações TypeScript, três plugins built-in com
source completo e testes, e 718 KB de changelog.

## Nota de escopo e licença

O repositório **não** contém o código-fonte do produto. O binário é um ELF de ~230 MB,
proprietário. Esta pesquisa:

- **usa**: o contrato publicado (`mods/types/claude-code.d.ts`), o source dos três mods, os
  13 plugins, os exemplos de settings/MDM/gateway, os workflows de CI, o `CHANGELOG.md`, os
  docs oficiais, e a observação dos artefatos que a instalação local escreve em disco;
- **não usa**: desmontagem, descompilação ou extração de strings do binário; nem conteúdo de
  sessão do usuário; nem credenciais.

Os padrões descritos aqui são **estudáveis, não reutilizáveis como código** — a licença não
permite.

## Índice

| # | Arquivo | Conteúdo |
|---|---|---|
| 01 | [Visão geral e superfície](01_visao_geral_superficie.md) | O produto, o que o repo é e não é, licença, o que é público × gerado × fechado |
| 02 | [O modelo engine/hooks](02_modelo_engine_hooks.md) | `$` / `on` / `next`, os cinco tiers, a inversão que faz toda chamada ser evento, `engine.create` |
| 03 | [A superfície de eventos](03_event_surface.md) | Catálogo: 19 substantivos, 34 eventos do engine, 50 chamadas em `$`, 33 hooks clássicos |
| 04 | [O loop do agente](04_agent_loop_turn.md) | `turn.start/step/complete`, streaming tipado, `session.compact`, `session.receive` |
| 05 | [Sistema de ferramentas](05_sistema_tools.md) | `describe` / `check` / `call`, o veredito `allow\|ask\|deny`, registro de ferramenta |
| 06 | [Permissões e segurança](06_permissoes_seguranca.md) | As quatro camadas: regras, veredito em código, sandbox, assento. MDM |
| 07 | [Prompt, contexto e memória](07_prompt_contexto_memoria.md) | System prompt por seção nomeada, custo de cache declarado no contrato |
| 08 | [Plugins e mods](08_plugins_e_mods.md) | As duas gerações de extensibilidade, `hooks.json`, marketplace, os 13 plugins |
| 09 | [`mods/diff` dissecado](09_mod_diff.md) | 779 arquivos: a fachada `Host`, estado em closure, negar evento, teste de custo |
| 10 | [`mods/telemetry` dissecado](10_mod_telemetry.md) | Estender o `$` em 45 linhas; opt-out recomputado a cada chamada |
| 11 | [`mods/sec-default` dissecado](11_mod_sec_default.md) | Segurança como posição na cadeia; 33 linhas, três movimentos |
| 12 | [O kit de teste](12_testing_kit.md) | O teste **é** o plugin do fundo; `mock.clock` com `advance`/`settle` |
| 13 | [MCP](13_mcp.md) | `$.mcp.call` como concessão estrutural, namespace compartilhado, o gateway |
| 14 | [Subagentes, skills e comandos](14_subagentes_skills_comandos.md) | `agent.offer/spawn`, `CommandSpec`, `skill.prompt`, agentes como arquivo |
| 15 | [Configuração e settings](15_config_settings.md) | Cinco fontes de settings × as linhas do `/config`; proveniência `bridge` |
| 16 | [O runtime observado em disco](16_runtime_local_observado.md) | Esquema do JSONL de transcrição, subagente com transcrição própria, `jobs/`, `file-history/` |
| 17 | [O que o CHANGELOG conta](17_evolucao_changelog.md) | 5.768 entradas, 52% correções; onde um harness de agente realmente quebra |
| 18 | [O harness em CI](18_ci_dogfooding.md) | O repo usando o próprio Claude Code: wrappers, teto de chamadas, credencial federada |
| 19 | [Comparativo com opencode](19_comparativo_opencode.md) | Dois desenhos lado a lado; onde cada um ganha |
| 20 | [Implicações para o harness Capella](20_implicacoes_harness_capella.md) | O que adotar, em que ordem, e o que descartar |
| 21 | [Fontes](21_fontes.md) | Pin, inventário e limites declarados |

## Leitura recomendada por objetivo

- **Entender a arquitetura em 20 minutos**: [02](02_modelo_engine_hooks.md) →
  [03](03_event_surface.md) → [04](04_agent_loop_turn.md)
- **Escrever um plugin/mod**: [02](02_modelo_engine_hooks.md) →
  [08](08_plugins_e_mods.md) → [09](09_mod_diff.md) → [12](12_testing_kit.md)
- **Política de segurança de uma organização**: [06](06_permissoes_seguranca.md) →
  [11](11_mod_sec_default.md) → [15](15_config_settings.md)
- **Rodar agente headless sem supervisão**: [18](18_ci_dogfooding.md) →
  [06](06_permissoes_seguranca.md) → [16](16_runtime_local_observado.md)
- **Projetar harness próprio** (o objetivo deste projeto): [20](20_implicacoes_harness_capella.md),
  com [19](19_comparativo_opencode.md) ao lado; as outras por referência conforme citado
- **Minerar transcrições de sessão**: [16](16_runtime_local_observado.md) →
  [04](04_agent_loop_turn.md)

## Os cinco achados centrais

Se só couber uma página:

1. **Não há duas superfícies.** Uma chamada em `$` é um evento que os hooks acima veem. Isso
   colapsa API, interceptação, sandbox e mock num mecanismo só. ([02](02_modelo_engine_hooks.md))
2. **Autoridade é assento, não código.** Cinco tiers, `next.to` só para dentro, e um mod de
   33 linhas que restaura a política da organização sem adicionar política nenhuma.
   ([11](11_mod_sec_default.md))
3. **O contrato documenta comportamento, não só tipos.** O que é pinado, o que é cacheado, o
   custo de cache de prompt de um hook instável, o que acontece quando um hook falha — tudo
   no docstring do evento. ([03](03_event_surface.md), [07](07_prompt_contexto_memoria.md))
4. **Proveniência é dado de primeira classe**, escrita pelo host e não falsificável por
   plugin — inclusive a distinção entre "a pessoa pediu" e "chegou por um canal que não prova
   quem é". ([15](15_config_settings.md))
5. **Metade do changelog é correção**, concentrada em multi-agente, background, IDE e MCP.
   O loop de um agente não é o problema difícil; o segundo agente é.
   ([17](17_evolucao_changelog.md))
