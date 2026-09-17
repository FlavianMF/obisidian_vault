---
title: Plugins e mods — duas gerações de extensibilidade
type: project
tags: [claude-code, plugins, extensibility, marketplace]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Plugins, mods e marketplaces

[← Índice](00_indice.md)

Duas gerações de extensibilidade convivem no mesmo repositório, e o nome delas confunde:

| | **Plugin** (clássico) | **Mod** |
|---|---|---|
| O que é | Pasta com comandos, agentes, skills, hooks declarativos, `.mcp.json` | Plugin cujo comportamento vive num **módulo de hooks** TypeScript |
| Como se estende | Arquivos Markdown + JSON + scripts externos | `register(on, options)` com hooks `($, e, next)` |
| Onde roda | Processo externo (`command`), ou conteúdo injetado | Ambiente próprio, sem Node, acesso ao mundo só via `$` |
| Exemplos no repo | `plugins/` — 13 plugins | `mods/` — `diff`, `telemetry`, `sec-default` |
| Distribuição | Marketplace, `/plugin` | Embutido no binário |

**Um mod é um plugin**, no sentido estrito: tem `.claude-plugin/plugin.json`, tem
`hooks/hooks.json`, e `claude --plugin-dir mods/diff` carrega qualquer um deles. A diferença é
o que o `hooks.json` contém — `"modules": ["./register.ts"]` em vez de uma tabela de eventos
clássicos.

## Estrutura de pasta

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # metadados
├── commands/                # slash commands (opcional)
├── agents/                  # agentes especializados (opcional)
├── skills/                  # Agent Skills (opcional)
├── hooks/                   # handlers de evento (opcional)
├── .mcp.json                # servidores MCP (opcional)
└── README.md
```
(`plugins/README.md`.)

`plugin.json` mínimo, como o do mod `diff`:
```json
{ "name": "diff", "version": "0.1.0", "description": "...", "author": { "name": "Anthropic" } }
```
Mais o campo `"types"` quando o plugin adiciona um substantivo ao `$`
([10](10_mod_telemetry.md)).

## `hooks.json`: as duas formas

**Forma de módulo** (mod):
```json
{ "description": "...", "modules": ["./register.ts"] }
```

**Forma clássica** (plugin), aqui a do `ralph-wiggum`:
```json
{
  "hooks": {
    "Stop": [ { "hooks": [ { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/stop-hook.sh" } ] } ]
  }
}
```

`${CLAUDE_PLUGIN_ROOT}` é a variável que resolve a raiz do plugin — o caminho absoluto nunca
é escrito.

### A forma clássica cresceu bastante

O `security-guidance` mostra o estado da arte da tabela clássica
(`plugins/security-guidance/hooks/hooks.json`):

| Chave | Efeito |
|---|---|
| `matcher` | Filtro por ferramenta: `"Edit\|Write\|MultiEdit\|NotebookEdit"` |
| `if` | Condição no formato de regra de permissão: `"Bash(git commit:*)"` |
| `timeout` | Segundos (o `SessionStart` dele usa 180) |
| `asyncRewake` | O hook roda em background e **reacorda a sessão** quando termina |
| `rewakeMessage` | O texto com que a sessão é reacordada |
| `rewakeSummary` | Rótulo curto do reacordar |

`asyncRewake` é o mais interessante: uma revisão de segurança roda em paralelo depois de um
`git commit`/`git push`, e o resultado volta como uma mensagem no meio da sessão —
"resolva ou reconheça os achados abaixo, depois continue com o pedido original do usuário".
Hook deixou de ser síncrono-bloqueante.

### O protocolo de saída de um hook clássico

Do `ralph-wiggum/hooks/stop-hook.sh`, que é o exemplo mais legível:

- Entrada: **JSON no stdin** (inclui `transcript_path`).
- Saída: JSON no stdout —
  ```json
  { "decision": "block", "reason": "<texto devolvido ao Claude>", "systemMessage": "<linha para a pessoa>" }
  ```
- `exit 0` sempre que o hook funcionou; deixar passar é sair sem bloquear.

O plugin lê a transcrição JSONL diretamente (`grep '"role":"assistant"' | tail -1 | jq ...`)
para pegar a última resposta — o mesmo formato descrito em
[16](16_runtime_local_observado.md). E o estado dele é um arquivo de markdown com
frontmatter em `.claude/ralph-loop.local.md`, com `iteration`, `max_iterations` e
`completion_promise`.

Vale registrar como **contraste** com o modelo de mods: aqui o plugin faz parsing de JSONL,
`sed` em frontmatter, escrita atômica com arquivo temporário, e validação manual de campo
numérico — trabalho que no modelo novo seria `$.store.get/set` e `$.session.messages()`.
O `stop-hook.sh` gasta a maior parte das suas ~180 linhas em tratamento de corrupção de
estado.

## Os 13 plugins do repo

`plugins/`, indexados em `.claude-plugin/marketplace.json` sob a marketplace
`claude-code-plugins`, com `category` por plugin:

| Plugin | Categoria | O que traz |
|---|---|---|
| `agent-sdk-dev` | development | `/new-sdk-app`, 2 agentes verificadores (py/ts) |
| `claude-opus-4-5-migration` | development | Skill de migração de model strings e beta headers |
| `code-review` | productivity | `/code-review` com 5 agentes paralelos e pontuação por confiança |
| `commit-commands` | productivity | `/commit`, `/commit-push-pr`, `/clean_gone` |
| `explanatory-output-style` | learning | Hook `SessionStart` injetando contexto educativo |
| `feature-dev` | development | `/feature-dev`, fluxo de 7 fases, 3 agentes |
| `frontend-design` | development | Skill auto-invocada para trabalho de frontend |
| `hookify` | productivity | Cria hooks a partir de conversa; agente `conversation-analyzer` |
| `learning-output-style` | learning | Hook `SessionStart` pedindo contribuição de código |
| `plugin-dev` | development | 7 skills + 3 agentes + `/plugin-dev:create-plugin` |
| `pr-review-toolkit` | productivity | 6 agentes de revisão + `/review-pr` |
| `ralph-wiggum` | development | Loop auto-referencial via hook `Stop` |
| `security-guidance` | security | Hooks Python: 9 padrões + revisão por LLM |

Dois deles — `explanatory-output-style` e `learning-output-style` — existem para **imitar
output styles descontinuados** ("deprecated"/"unshipped") usando só hook de `SessionStart`.
É um bom indicador da expressividade do sistema: um recurso removido do produto foi
reimplementado como plugin de fora.

## Marketplace

`.claude-plugin/marketplace.json`, com `$schema` público
(`https://json.schemastore.org/claude-code-marketplace.json`):

```json
{
  "name": "claude-code-plugins",
  "owner": { "name": "Anthropic", ... },
  "plugins": [ { "name": "...", "source": "./plugins/...", "category": "...", "version": "...", "author": {...} } ]
}
```

`source` é um caminho relativo dentro do próprio repositório: uma marketplace é só um
manifesto que aponta pastas. Nada de registry central obrigatório.

## Comandos de plugin

Do `mods/README.md` e do `plugins/README.md`:

| Comando | Para quê |
|---|---|
| `claude --plugin-dir <dir>` | Carrega um plugin a partir do source, sem instalar |
| `claude plugin test <dir>` | Roda os testes do plugin ([12](12_testing_kit.md)) |
| `/plugin` | Instala a partir de marketplaces |
| `/plugin-types` | Regenera `.claude/types/claude-code.d.ts` para a versão instalada |
| `/reload-plugins` | Recarrega (dispara `session.start` só daquele plugin) |

## Ordem de carga e recarga

Dois fatos do contrato que importam para quem desenvolve:

- `plugin.register` e `session.start` disparam **uma vez por processo para cada plugin
  carregado, antes do primeiro prompt**, e de novo para um que carregue ou recarregue depois.
  **O primeiro é aguardado**, então um `$.tool.register` ali já é listado no turno um
  (`claude-code.d.ts:3106-3113`).
- Uma recarga (edição, opções novas, `/reload-plugins`, um enable) roda os hooks **só daquele
  plugin**, então os timers dele recomeçam. `/clear` **não** é recarga.

E as opções: "são fixas para esta ativação: uma mudança nelas recarrega o plugin e
`register` roda de novo com o objeto novo. Os hooks fecham sobre ele" (`Register`,
`claude-code.d.ts:5901`). Não existe "ler config no meio" — config muda ⇒ plugin reinicia.

## Ver também

- [02](02_modelo_engine_hooks.md) — o modelo de mods
- [14](14_subagentes_skills_comandos.md) — comandos, agentes e skills em detalhe
- [09](09_mod_diff.md) — um mod real, inteiro
