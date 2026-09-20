---
title: Skill Monolítica Gasta o Contexto Antes de a Tarefa Começar
type: trap
tags: [agentic-ai, skills, claude-code, context-management, prompt-engineering, armadilha]
created: 2026-09-20
provenance: taste-skill
verified: 2026-09-20 via wc -c em ~/.agents/skills/*/SKILL.md e ~/.claude/skills/impeccable/
---

# Skill Monolítica Gasta o Contexto Antes de a Tarefa Começar

**Uma skill cujo método inteiro mora num único `SKILL.md` cobra o arquivo inteiro assim
que é acionada, mesmo que a tarefa use um décimo dele.** O custo aparece antes de qualquer
trabalho e não é recuperável na sessão.

Medição, não impressão. Em `~/.agents/skills/`, depois de instalar a [[Taste Skill]]:

| Skill | `SKILL.md` | linhas |
|---|---|---|
| `design-taste-frontend` | 87.253 B | 1206 |
| `imagegen-frontend-mobile` | 40.326 B | 1465 |
| `imagegen-frontend-web` | 36.854 B | 987 |
| `image-to-code` | 36.442 B | 1228 |

O pacote inteiro são 15 arquivos, e o único que não é um `SKILL.md` é
`stitch-design-taste/DESIGN.md`. Nenhuma das 13 skills tem `reference/`, `scripts/` ou
`assets/`. A maior custa da ordem de 20k tokens por sessão em que é carregada.

O contraste está no mesmo disco: [[Impeccable]] tem `SKILL.md` de 11.896 B que quase não
contém método — ele roteia — mais 36 entradas em `reference/` (452 KB) carregadas sob
demanda, com `new-work.md` e `critique.md` só entrando no contexto quando o comando
correspondente é pedido. Mesma ordem de grandeza de conhecimento, custo pago por uso.

## O agravante

A própria Taste declara em `SKILL.md:896` que **dashboard e UI densa de produto, data
table, formulário multi-etapa, editor de código, mobile nativo e UI de colaboração em
tempo real estão fora de escopo**, cada um com um encaminhamento para outra ferramenta.
Carregá-la nesses casos é custo integral com zero regra aplicável. A stack pressuposta é
React/Next + Tailwind v4: não há suporte de primeira mão a Vue, Svelte, Angular ou Solid.

## Como detectar

```bash
wc -c ~/.claude/skills/*/SKILL.md ~/.agents/skills/*/SKILL.md | sort -n | tail
ls ~/.agents/skills/<nome>/        # sem subdiretório = monolítica por construção
```

Acima de ~30 KB num único arquivo, vale checar se o método tem modos ou comandos
separáveis. Se tem, o arquivo está pagando tudo para usar uma parte.

## O que fazer

- **Acionar por tipo de artefato, nunca especulativamente.** Landing, portfólio e redesign
  em React/Tailwind justificam a Taste; o resto não.
- **Ao escrever skill própria, separar roteador de playbook.** O `SKILL.md` carrega os
  princípios, a tabela de comandos e o critério de escolha; o método de cada comando vive
  num arquivo lido quando aquele comando é pedido.
- Regra de partição complementar, de [[Detector Determinístico Fora do LLM como Piso de Qualidade]]:
  o que um programa consegue checar nem deveria estar no prompt.

## 🔗 Conexões

- [[Impeccable]] — a arquitetura oposta, roteador mais referência sob demanda.
- [[claude-code]] e [[07_prompt_contexto_memoria|Prompt, contexto e memória]] — onde o
  orçamento de contexto é gasto.
- [[Skills de Design se Contradizem Entre Si, Dentro e Fora do Pacote]] — a outra
  armadilha de instalar um pacote inteiro de uma vez.
