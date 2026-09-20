---
title: Uma Fonte de Regra, N Harnesses Compilados
type: pattern
tags: [agentic-ai, prompt-engineering, claude-code, distribution, hooks, skills]
created: 2026-09-20
provenance: impeccable
---

# Uma Fonte de Regra, N Harnesses Compilados

**Prompt de skill que precisa rodar em vários harnesses é artefato compilado, não arquivo
copiado: uma fonte única, um build por alvo, e patches por modelo aplicados no build.**
[[Impeccable]] mantém `skill/SKILL.src.md` mais `skill/reference/` como fonte e gera
`dist/<provider>/` para Claude Code, Cursor, Codex, GitHub Copilot, Gemini, Grok Build e
mais de dez outros. O binário do detector é o mesmo em todas as distribuições; o que muda
é o envelope.

## Três coisas variam por alvo

**1. Placeholders de caminho e de invocação.** A fonte escreve `{{scripts_path}}` e
`{{command_prefix}}`; o build resolve para o layout daquele harness. A instalação de Claude
Code vira `.claude/skills/impeccable/scripts/impeccable`.

**2. O manifest de hook, que é semanticamente diferente por harness** — e essa é a parte
que não dá para abstrair:

| Harness | Evento | Comportamento |
|---|---|---|
| Claude Code, Codex | `PostToolUse` + `Stop` | edição passa; lembrete injetado no contexto depois |
| Cursor | `preToolUse` | **bloqueia** a escrita proposta antes de ela cair no disco |
| Grok Build | `PostToolUse` + `Stop` | marca arquivos tocados; achados só no `additionalContext` do Stop, porque o Grok descarta o stdout do per-edit |
| GitHub Copilot | hook commitado em `.github/` | eventos de parada não devolvem contexto ao modelo, então o conjunto completo de regras roda a cada edição |

Onde o `Stop` não é despachado de forma confiável, o passe profundo simplesmente não
existe e a compensação é outra (o gate de pré-escrita do Cursor cobre o caso). Quando não
há hook nenhum, o setup emite uma diretiva `MANUAL_DETECTOR_REQUIRED` pedindo uma rodada
manual no fim. **Degradação declarada, não silenciosa.**

**3. Patch de viés por modelo.** A fonte carrega blocos `<claude>`, `<codex>` e `<gemini>`
que só entram na build daquele modelo, e o conteúdo deles é correção de tendência
**medida**, não conselho genérico. O bloco `<claude>`, textualmente, avisa que a rendição
padrão do Claude para assunto acolhedor ou infantil sai em fundo creme, serifa display em
itálico e luz de abajur mesmo quando a direção não pediu — e manda tratar essa primeira
paleta como já gasta. O bloco `<codex>` trata de tracking, elevação dupla e SVG
imitando ilustração. O `<gemini>` é uma linha sobre animar imagem no hover.

## Por que isso é um padrão e não um detalhe de build

Tratar prompt como código-fonte compilável dá três coisas que copiar-e-colar não dá:
a regra existe **uma vez** (corrigir significa corrigir em um lugar); a diferença entre
alvos fica **explícita e revisável** em vez de derivar; e o viés específico de um modelo
vira **dado versionado** em vez de folclore. Ver
[[Autoridade por Assento na Cadeia de Hooks]] para o lado de política da mesma cadeia, e
[[claude-code]] / [[opencode]] para os harnesses em si.

## Generaliza

Vale para qualquer instrução que precise viver em mais de um runtime de agente: regra de
projeto (`CLAUDE.md` / `AGENTS.md` / `.cursorrules`), definição de ferramenta, política de
permissão. A pergunta de arquitetura é sempre a mesma — **o que é a regra, o que é o
envelope do harness, e o que é correção de um modelo específico?** Misturar os três num
arquivo só é o que torna a manutenção impossível depois do segundo alvo.
