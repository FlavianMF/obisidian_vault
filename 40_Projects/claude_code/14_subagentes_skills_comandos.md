---
title: Subagentes, skills e comandos
type: project
tags: [claude-code, multi-agent, subagents, skills, commands]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Subagentes, skills e comandos

[← Índice](00_indice.md)

Três formas de "unidade de comportamento" que o harness expõe. As três passam pelos mesmos
eventos, e as três podem vir de um plugin.

## Subagentes

### `agent.offer` — o que o modelo sequer sabe que existe

```ts
type AgentOfferInput = { agent: string; description: string; source: string; provider: Origin }
type AgentOfferResult = { isOffered: boolean }
```
`claude-code.d.ts:154` e `180`.

Dispara para decidir se um tipo de agente é **oferecido ao modelo**, na listagem e no
despacho. O exemplo no próprio contrato é desligar um agente built-in:

```ts
on("agent.offer", { agent: "Plan" }, () => ({ isOffered: false }))
```
(`claude-code.d.ts:2954`.)

Os quatro campos cobrem eixos diferentes de política:
- `agent` — o tipo (`Explore`, `Plan`, o agente de um plugin);
- `description` — a linha de listagem, "como a definição a declara (`whenToUse`)";
- `source` — de onde veio a definição (`built-in`, `plugin`, uma fonte de settings), "para
  que um matcher distinga um built-in do agente de um usuário com o mesmo nome";
- `provider` — **pinado**, `{ plugin, tier }` de quem fornece.

Esse último é o que o `sec-default` usa para impedir que um plugin de usuário esconda um
agente instalado pela organização ([11](11_mod_sec_default.md)).

### `agent.spawn` — o nascimento

Dispara "quando a ferramenta Agent está prestes a iniciar um subagente, tudo decidido e o
modelo dele ainda não resolvido". `next(e)` resolve `{ model }`; um hook pode devolver isso,
`next({ ...e, model })`, um `{ model }` próprio (um alias resolve como o parâmetro da
ferramenta), ou `{ deny: reason }` (`claude-code.d.ts:2956-2965`).

`AgentSpawnInput` (`claude-code.d.ts:201`) tem 13 campos, e a lista é reveladora do que um
subagente é neste harness:

| Campo | O que diz |
|---|---|
| `tool_use_id`, `prompt`, `description`, `subagentType` | a chamada |
| `provider: Origin` | quem fornece o tipo de agente |
| `model?`, `parentModel` | modelo pedido e o do pai |
| `parentAgentId?` | o loop que gerou; ausente no main |
| `permissionMode?` | modo de permissão próprio |
| `background: boolean` | roda em background |
| `fork: boolean` | é um fork da conversa |
| `name?`, `cwd?` | rótulo e diretório próprios |

`cwd` e `permissionMode` próprios significam que um subagente **não** é só uma sub-chamada de
LLM: é um loop com ambiente e política possivelmente diferentes do pai.

Quando um plugin chama `$.agent.spawn` diretamente, "o spawn de uma chamada roda em
background: ela resolve assim que o subagente começou, e nada a segura em primeiro plano"
(`claude-code.d.ts:191-199`), devolvendo `AgentCallRecord = { agentId, resolvedModel? }`
(`claude-code.d.ts:73`).

### Quem é quem depois

`$.agent.list()` devolve `AgentInfo` (`claude-code.d.ts:88`): `id`, `description`, `type`
(`general-purpose`, `Explore`, … ou `teammate` para um teammate in-process), `status`
(`running`, `completed`, `failed`, `killed`), `parentId`, e `spawnedBy` — "o plugin cujo
`$.agent.spawn` (ou `tool.call` de Agent) o iniciou; ausente quando foi o modelo ou a pessoa".

Dois eixos separados de novo: **hierarquia** (`parentId`) e **origem** (`spawnedBy`).

### A regra anti-recursão

Do contrato de `turn.step` (`claude-code.d.ts:8556-8559`):

> Um subagente que um hook gerou por `$.agent.spawn` **pula aquele hook** nos seus passos,
> como fazem as chamadas de ferramenta dele; todo outro hook vê os passos dele.

Sem isso, um hook que gera subagente ao ver um `turn.step` geraria subagentes infinitamente.
A proteção está no engine, não na disciplina do autor do plugin.

## Comandos

```ts
type CommandSpec = {
  name: string          // sem a barra; letras, dígitos, _ , - ; até 64
  description: string   // a linha do typeahead e do /help
  argumentHint?: string // o hint dim depois do nome
  immediate?: true
}
```
`claude-code.d.ts:1359`.

`immediate` é o campo com consequência:

> Defina para que `/<name>` digitado **enquanto um turno está em voo** rode na hora, em vez
> de esperar o turno acabar, como acontece quando não é definido. O hook `command.run` dele
> roda então enquanto um turno ainda pode estar streamando e **não deve assumir o estado do
> turno** (o que a transcrição tem, se uma ferramenta está no meio de uma chamada).

Registro é `$.command.register(spec)` — evento `command.register`. Execução é `command.run`,
com matcher pelo nome, e o `diff` usa os dois lados: registra `/diff` no `session.start` e
hooka `command.run` para `{ command: ['clear','resume'] }` **de outros comandos** para
resetar seu estado ([09](09_mod_diff.md)).

`command.describe` existe à parte, e é um dos eventos que o `sec-default` protege — porque a
descrição é o que chega ao modelo.

Na forma clássica, um comando é um `.md` com frontmatter
(`plugins/pr-review-toolkit/commands/review-pr.md`):

```yaml
---
description: "Comprehensive PR review using specialized agents"
argument-hint: "[review-aspects]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Task"]
---
```

`$ARGUMENTS` no corpo recebe o que a pessoa digitou. `allowed-tools` restringe o que o
comando pode usar — política declarada junto com o prompt.

## Skills

```ts
type SkillPromptInput  = { skill: string; text: string }
type SkillPromptResult = { text: string }
```

Um evento só, e minimalista: `skill` é qual skill, `text` é "o texto do prompt como a skill o
computou (seus blocos de texto, juntados)". O hook devolve o texto que o modelo lê.

Isto é o ponto de intervenção sobre **conteúdo de skill**, e é justamente um dos quatro que o
`sec-default` empurra para além do tier do usuário, ao lado de `prompt.section`,
`prompt.context` e `attribution.text` — para que skills de política de uma organização
cheguem ao modelo como escritas.

Na forma clássica, uma skill é `skills/<nome>/SKILL.md` com frontmatter
(`plugins/plugin-dev/skills/hook-development/SKILL.md`):

```yaml
---
name: Hook Development
description: This skill should be used when the user asks to "create a hook", ...
version: 0.1.0
---
```

A `description` é escrita como **gatilho**, enumerando as frases que devem ativá-la — não como
resumo. É assim que as 7 skills do `plugin-dev` são escritas.

## Agentes na forma clássica

`agents/<nome>.md` com frontmatter
(`plugins/pr-review-toolkit/agents/silent-failure-hunter.md`):

```yaml
---
name: silent-failure-hunter
description: Use this agent when ... Examples: <example>...</example>
model: inherit
color: yellow
---
```

Observações úteis:
- `model: inherit` — o agente herda o modelo da sessão em vez de pinar um.
- A `description` embute **exemplos de diálogo completos** em tags `<example>`, mostrando o
  turno do usuário e a resposta esperada do assistente. É prompt engineering de roteamento,
  não documentação.
- O corpo é a persona e o processo do agente, em Markdown.

O `pr-review-toolkit` tem 6 desses (`comment-analyzer`, `pr-test-analyzer`,
`silent-failure-hunter`, `type-design-analyzer`, `code-reviewer`, `code-simplifier`), e o
comando `/review-pr` os despacha em paralelo via a ferramenta `Task`.

## O padrão de composição do repo

Olhando os 13 plugins juntos, o idioma recorrente é:

> **um comando que orquestra + vários agentes especializados que rodam em paralelo + skills
> que carregam o conhecimento**

`code-review` (5 agentes paralelos com pontuação por confiança para filtrar falsos
positivos), `feature-dev` (3 agentes, 7 fases), `pr-review-toolkit` (6 agentes), `plugin-dev`
(3 agentes + 7 skills). O comando não faz o trabalho: ele decide quem faz.

## Ver também

- [04](04_agent_loop_turn.md) — `agentId` no loop
- [08](08_plugins_e_mods.md) — como isso é empacotado
- [07](07_prompt_contexto_memoria.md) — `skill.prompt` entre os eventos de prompt
