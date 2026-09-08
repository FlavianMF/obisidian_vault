---
title: Multi-agente e subagentes
type: project
tags: [opencode, multi-agent, subagents]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

> Ver [[opencode]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Multi-agente e subagentes

[← Índice](00_indice.md)

Feature de primeira classe, análoga à tool Task do Claude Code. Docs: [opencode.ai/docs/agents](https://opencode.ai/docs/agents/) · Fonte: `packages/opencode/src/tool/task.ts`, `packages/opencode/src/agent/*`

## Agentes built-in

- **Primários:** `build` (acesso completo, padrão), `plan` (edits/bash default para `"ask"`)
- **Subagentes:** `general` (acesso amplo menos todo), `explore` (só leitura), `scout` (só leitura, pesquisa de docs/deps externos)
- **Agentes de sistema ocultos:** compaction, title, summary

## Agentes customizados

JSON em `opencode.json` sob `"agent"`, ou arquivos Markdown com frontmatter YAML em `.opencode/agents/` (projeto) / `~/.config/opencode/agents/` (global). Campos: `mode` (`primary`|`subagent`|`all`), `model`, `temperature`, `steps` (máximo de iterações agênticas), `permission`, `permission.task` (padrão glob que restringe quais tipos de subagente esse agente pode invocar), `hidden`, `color`.

## Mecânica da tool `task`

De `task.ts`, comportamento exato:

- Parâmetros: `description`, `prompt`, `subagent_type`, opcional `task_id` (retomar sessão de subagente anterior em vez de criar nova), opcional `command`, opcional `background` (boolean — requer `OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS=true`)
- **Limite de profundidade:** sobe a cadeia de `parentID` e falha se profundidade ≥ `config.subagent_depth` (padrão 1) — "Increase `subagent_depth` to allow nested subagents."
- Invocar uma task passa pelo mesmo fluxo de permissão **`ask`** de qualquer tool call (`permission: "task"`, padrão = `subagent_type`)
- Sessão filha criada com **permissões derivadas/restritas** (`deriveSubagentSessionPermission`) mais deny explícito para `todowrite` e `task` (a própria tool), a menos que a config de permission do subagente reabilite explicitamente — ou seja, subagentes não podem recursivamente criar mais subagentes ou escrever todos a menos que explicitamente permitido
- `config.experimental.primary_tools` pode negar tools específicas para subagentes globalmente
- **Modo background:** task dispara async, notifica a sessão pai automaticamente na conclusão via mensagem sintética injetada (`renderOutput` com tags `<task_result>`/`<task_error>`); instrução explícita embutida dizendo ao modelo para **não** fazer polling/sleep esperando status
- Invocação manual via `@subagent-name` na conversa; invocação automática é dirigida pelo modelo com base na `description` do agente

## Navegação da árvore de sessão

Na TUI: Down (entra na sessão filha do subagente), Up (pai), Left/Right (filhos irmãos). Via API: `GET /session/{id}/children` expõe a árvore — útil se um harness quiser visualizar/logar o fan-out de subagentes.

## Ver também

- [03_agent_loop.md](03_agent_loop.md) — como a tool `task` se encaixa no loop de execução
- [07_permissoes_seguranca.md](07_permissoes_seguranca.md) — permissão `task` como gate
- [12_headless_sdk_api.md](12_headless_sdk_api.md) — rota `GET /session/{id}/children`
