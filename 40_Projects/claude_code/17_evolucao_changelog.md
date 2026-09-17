---
title: O que o CHANGELOG conta — 5768 entradas
type: project
tags: [claude-code, evolution, changelog, engineering-cost]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# O que o CHANGELOG conta

[← Índice](00_indice.md)

`CHANGELOG.md` tem **718 KB**, **397 versões** e **5.768 entradas**, de `0.2.21` até `2.1.274`.
É a fonte mais densa do repositório sobre o que o harness virou — e sobre o que custa
manter um.

## O perfil das mudanças

| Prefixo | Entradas | % |
|---|---:|---:|
| `Fixed` | 3.009 | 52% |
| `Added` | 598 | 10% |
| `Improved` | 529 | 9% |
| `Changed` | 204 | 4% |
| `Removed` | 35 | 0,6% |
| `Deprecated` | 9 | — |
| `Restored` | 3 | — |

(Os ~24% restantes são entradas sem prefixo padronizado, comuns nas versões antigas.)

**Metade do changelog é correção.** E a leitura das correções é o que torna o arquivo útil
como documento de engenharia: elas dizem onde um harness de agente realmente quebra.

Distribuição por série: `2.1` tem 219 versões, `2.0` tem 59, `1.0` tem 82, `0.2` tem 37.
Não há datas — só números de versão.

## Onde as correções se concentram

Contagem de menções ao longo do arquivo inteiro:

| Tema | Menções |
|---|---:|
| subagente / agente | 696 |
| IDE (VSCode, JetBrains) | 636 |
| background | 434 |
| MCP | 411 |
| permissão | 338 |
| plugin | 331 |
| Windows | 225 |
| hook | 231 |
| skill | 200 |
| Remote Control | 159 |
| Bedrock / Vertex / Foundry | 154 |
| worktree | 123 |
| managed settings / política | 118 |
| compactação | 117 |
| cloud / Cowork | 98 |
| sandbox | 96 |
| OpenTelemetry | 59 |
| Artifact | 42 |
| schedule / routine | 43 |

Três leituras:

1. **Multi-agente e execução em background são a maior fonte de complexidade.** 696 + 434
   menções. Não é o loop de um agente que é difícil — é o segundo agente.
2. **MCP custa caro** (411). Em [13](13_mcp.md) estão os eixos: transporte, negociação de
   protocolo, OAuth, timeout de startup, `list_changed`, vazamento de `${VAR}`.
3. **Superfícies externas** (IDE 636, Windows 225, Remote Control 159, providers 154) somam
   mais que o núcleo. Um harness que roda em um lugar só é um problema muito menor.

## As linhas de evolução visíveis

### De um agente para muitos

O vocabulário do produto cresceu em camadas: subagente, tarefa em background, **teammate**,
sessão em cloud. As três últimas aparecem nos hooks clássicos como `TaskCreated`,
`TaskCompleted`, `TeammateIdle`, `SubagentStart`, `SubagentStop`
([03](03_event_surface.md)), e o changelog registra a introdução:

> Added `TeammateIdle` and `TaskCompleted` hook events for multi-agent workflows

E o painel: `claude agents` com `--add-dir`, `--settings`, `--mcp-config`, `--plugin-dir`,
`--permission-mode`, `--model`, `--effort` para configurar sessões em background despachadas
dali. Ou seja: o harness virou um **dispatcher de sessões**, não só uma sessão.

### Worktree como primitiva do produto

123 menções, uma ferramenta própria (`EnterWorktree`), hooks (`WorktreeCreate`,
`WorktreeRemove`) e settings dedicados:

> Added `worktree.baseRef` setting (`fresh` | `head`) to choose whether `--worktree`,
> `EnterWorktree`, and agent-isolation worktrees branch from `origin/<default>` or local
> `HEAD`.

> Added `worktree.bgIsolation: "none"` setting to let background sessions edit the working
> copy directly without `EnterWorktree`, for repos where worktrees are impractical.

Isolamento de agente por worktree deixou de ser disciplina do usuário e virou mecanismo do
harness. (Relevante aqui: é a mesma disciplina que esta pesquisa usa no repo do projeto.)

### Sandbox virou granular

De "liga/desliga" para política por comando:

> Added per-command `allowed_domains` to Bash, PowerShell and Monitor in auto mode with
> sandboxing: **os hosts que um comando precisa são revisados junto com ele e abertos só para
> ele**; outros hosts são recusados.

E uma distinção de intenção que vale copiar:

> Changed commands typed at the `!` bash-mode prompt to run outside the sandbox even when
> strict sandbox mode is on, **like typing into your own terminal**.

O comando que a *pessoa* digita não é o comando que o *modelo* propõe, mesmo sendo a mesma
string. O harness trata proveniência como parte da política — o mesmo princípio de
`next.origin` ([02](02_modelo_engine_hooks.md)) e de `ConfigOrigin.bridge`
([15](15_config_settings.md)).

### Observabilidade: OpenTelemetry de verdade

59 menções, com spans, eventos e métricas nomeados:
`claude_code.llm_request` (span, com atributo `effort`), `claude_code.api_request`,
`claude_code.managed_settings_resolved`, e switches por variável:
`OTEL_LOG_TOOL_DETAILS`, `OTEL_LOG_MANAGED_SETTINGS`, `OTEL_METRICS_INCLUDE_REPOSITORY`
(taga métricas com atributos `vcs.*`).

> Added `message.uuid`, `client_request_id`, and `tool_source` attributes to OpenTelemetry
> log events for **message-level correlation and tool provenance**.

Isso é o canal externo; o `$.telemetry` do mod é o interno e first-party
([10](10_mod_telemetry.md)). Dois canais, propósitos distintos.

### Compactação como parâmetro de custo

> Changed Sonnet 5's default auto-compact window to its full 1M context, so sessions on the
> 1M window now auto-compact at about 967K tokens instead of about 934K.

> Changed `CLAUDE_CODE_DISABLE_1M_CONTEXT` to hold every Claude model with a native 1M window
> to 200K via auto-compaction, not just a fixed list.

E headers para gateways de LLM, opt-in por `CLAUDE_CODE_GATEWAY_HINT_HEADERS=1`:
`x-claude-code-request-class`, `x-claude-code-agent-type`,
`x-claude-code-prev-tool-durations`, `x-claude-code-compaction`,
`x-claude-code-context-compacted`. O harness **conta ao gateway** o que está fazendo, para
que o gateway possa rotear e cobrar com informação.

### `--plugin-dir` amadureceu junto com o sistema de plugins

Sequência legível no arquivo: aceitar uma pasta de plugins (cada subpasta com manifesto
carrega, e filhas adicionadas/removidas em runtime são pegas), aceitar `.zip`, restringir a
um caminho por flag (repetível), fazer cópia local de dev sobrepor plugin de marketplace com
o mesmo nome — **"a não ser que aquele plugin esteja force-enabled pelos managed settings"**.

Até o atalho de desenvolvimento respeita a autoridade da organização.

## O que o CHANGELOG **não** conta

Buscas por `function hook`, `hooks module`, `register(on`, `engine.create` e `mods` no
changelog **não retornam nada**. A API de mods/function hooks — o assunto central de
[02](02_modelo_engine_hooks.md) e [03](03_event_surface.md) — não é anunciada ali.

Bate com o aviso no topo do `.d.ts`: *EARLY ACCESS: esta superfície pode mudar entre releases
sem aviso* (`claude-code.d.ts:4`). A superfície nova é publicada como **código e tipos**, não
como release note.

Consequência prática para quem depender dela: o `CHANGELOG` não é o canal de alerta.
O canal é regenerar `claude-code.d.ts` com `/plugin-types` a cada atualização e comparar.

## Como ler 718 KB sem ler 718 KB

O método usado nesta pesquisa, reprodutível:

```bash
grep -cE '^## ' CHANGELOG.md                      # versões
grep -oE '^- (Added|Fixed|Changed|Improved)' CHANGELOG.md | sort | uniq -c | sort -rn
grep -icE 'MCP|sandbox|worktree|teammate' CHANGELOG.md   # peso por tema
grep -E '^- (Added|Changed).*<tema>' CHANGELOG.md | head # as entradas que definem o tema
```

`Added` e `Changed` contam a evolução; `Fixed` conta onde dói.

## Ver também

- [13](13_mcp.md) — o detalhe operacional de MCP extraído daqui
- [16](16_runtime_local_observado.md) — o que dessa evolução se vê em disco
- [19](19_comparativo_opencode.md) — o comparativo com o opencode
