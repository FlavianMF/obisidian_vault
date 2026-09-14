---
title: Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase
type: pattern
tags: [project-methodology, rfc, prd, documentation, agentic-ai, traceability, dev-workflow]
created: 2026-09-11
provenance: orbita-platform
project: orbita-platform
---

# Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase

Método de definição e condução de projeto destilado do `orbita-platform` (plataforma
financeira Next.js/Prisma), o primeiro projeto a levar a cadeia inteira até o fim: Fase 1
(MVP), Fase 2 (11 decisões de produto, 8 RFCs, 10 etapas mescláveis) e etapas pós-fase.
Complementa o [[Checklist de Bootstrap de Workflow de Desenvolvimento]]: **aquele governa
*como construir*** (worktree, gate de teste, CI, release); **este governa *o que construir,
em que ordem, e como provar que acabou***.

O ganho não é burocrático. É que qualquer sessão nova — agente ou humano — consegue
reconstruir o estado do projeto lendo documento, sem arqueologia de `git log`.

## A cadeia

| # | Artefato | Papel | Quem escreve |
|---|---|---|---|
| 1 | **Documento de intenção** | Prosa crua do usuário: o que ele quer, por quê, o que já imagina de solução. Versionado como está, sem edição | Usuário |
| 2 | **Escopo do sistema** | Entidades, relações, casos de uso `UC*`, atores — inclusive os futuros. Cada item tagueado com a fase que o entrega (`[MVP]`, `[Fase 2]`, `[Fase 3]`) | Agente, revisado |
| 3 | **Especificação de release / [[PRD]]** | Dentro vs. fora de escopo desta entrega, atividades `ACT-*`, modelo de dados, arquitetura | Agente, revisado |
| 4 | **RFC-000 — visão da fase** | Tabela de decisões `D1..Dn`, mapa das RFCs, fora de escopo, requisitos transversais, riscos com mitigação | Agente, em curadoria |
| 5 | **RFC temática** | Uma decisão técnica por documento, rastreada às decisões `Dn` que ela detalha. Ver [[RFC de Produto - Anatomia e Ciclo de Status]] | Agente |
| 6 | **Plano de fase** | `E0..En` mescláveis, diagrama de dependências, **Aceite** por etapa. Ver [[Plano de Fase em Etapas Mescláveis]] | Agente |
| 7 | **Nota de conclusão de etapa** | O que foi feito, achados, verificação, fora de escopo, próximos passos. Ver [[Nota de Conclusão de Etapa é Entregável, Não Relatório]] | Agente |
| 8 | **Playbook** | Tático e transversal: padrões validados e erros já cometidos. Ver [[Playbook de Projeto - Erros Já Cometidos Como Artefato]] | Agente, cresce sempre |
| 9 | **Índice (MOC)** | Enxuto. Uma linha por etapa com status, mais o prompt de início de sessão | Agente |

Fluxo de rastreabilidade, ponta a ponta:

```
intenção + escopo do sistema + PRD
      ↓  RFC-000 §2  →  decisões D1…Dn (datadas, atribuídas)
      ↓  cada Dn  →  a RFC que a detalha
      ↓  plano de fase  →  etapa En (RFCs, Depende, Aceite, worktree)
      ↓  nota de conclusão En (cita RFC §§ e a âncora do plano)
      ↓  branch worktree-<escopo> → PR #N → merge → tag
      ↑  achados da etapa sobem pro playbook, com link de volta
      ↑  Status da RFC é reescrito: "Implementado (En)"
      ↑  índice ganha a linha com ✅/🟡
```

## Escalonamento — três níveis

Aplicar a cadeia inteira num script de 200 linhas é teatro. O nível se decide **antes** de
escrever o primeiro documento, e se declara ao usuário:

**Nível 3 — produto multi-fase.** Cadeia completa (1→9). Gatilho: mais de um ator ou área,
banco de dados com dados de usuário real, trabalho distribuído em várias sessões/worktrees,
ou uma fase que já nasce com mais de ~5 entregas independentes.

**Nível 2 — serviço ou feature grande.** `PRD.md` curto + **uma** RFC (a visão cabe no topo
dela, sem RFC-000) + plano de etapas + playbook + índice. Gatilho: entrega única mas com
decisão técnica que alguém vai querer redebater depois.

**Nível 1 — script ou ferramenta.** Só `docs/PRD.md` de meia página (problema, dentro/fora,
critério de aceite) + playbook nascendo vazio. Sem RFC, sem plano de etapas. Gatilho: tudo
o mais.

Subir de nível no meio do caminho é normal e barato — o `PRD.md` do nível 1 vira a seção
"Contexto" do RFC-000. Descer não acontece: documento escrito não se apaga, se marca como
histórico.

## As oito propriedades que fazem funcionar

1. **Decisão tem número e dono.** `D5` aparece no RFC-000, na RFC que a detalha, no plano e
   na nota de etapa. Decisão revisada não é reescrita em silêncio: fica
   "**Revisada**: … (a decisão original era invite-only)" — quem lê seis meses depois vê a
   mudança, não só o resultado.
2. **Status mora no artefato**, não só no git. A RFC diz onde foi implementada
   (`Implementado (E0/E1 + revisado em E9a)`), o plano diz `✅ Concluído (data)` ou
   `🟡 aguardando validação`, o índice repete.
3. **Aceite é escrito antes da execução, em forma de teste negativo.** "O consultor vê
   apenas clientes com vínculo `ATIVO` — teste com `REVOGADO`" é aceite; "funcionar bem"
   não é.
4. **Etapa = worktree = PR = nota**, um para um para um para um. Etapa que não é mesclável
   sozinha está mal cortada.
5. **Fatiar sob demanda é normal.** Quando o diff fica grande demais para o usuário
   validar, `E8` vira `E8a`/`E8b`. A renumeração é registrada no plano com o motivo.
6. **"Fora de escopo" é seção obrigatória** — no RFC-000 e em cada nota de etapa. É o que
   impede o escopo de crescer por omissão.
7. **Achado vira playbook no mesmo ciclo**, com sintoma, causa e o comando que reproduz.
8. **Pergunte antes de adivinhar.** Pedido amplo ou subjetivo (redesenho visual,
   "modularidade", fonte de dado que não existe) rende 2–3 opções concretas ao usuário
   antes de qualquer implementação. Refazer depois de um palpite errado custa mais que
   perguntar — e a resposta vira a seção "Decisões confirmadas com o usuário nesta sessão"
   da nota da etapa.

## Taxonomia de pastas

`docs/` organizado por **natureza do documento**, não por cronologia:

```
docs/
├── index.md          MOC + prompt de início de sessão
├── escopo/           o quê: intenção, escopo do sistema, PRD, e escopo/rfc/
├── projeto/          como e quando: plano de fase, notas de etapa, playbook, operação
├── qualidade/        a régua: diretrizes de teste, quality gates, limites
├── dados/            modelo de dados
└── mbse/             capacidades operacionais (quando o projeto usa MBSE)
```

## Convenções de forma

- **Sem frontmatter YAML nos documentos de projeto** (o frontmatter é convenção do vault,
  não do repositório). A metadata é a **linha 3**, em negrito, separada por `·`.
- Um `# H1` por arquivo, igual ao título; parágrafo-resumo; `---`; seções numeradas à mão
  (`## 1.`, `### 1.1`).
- **`## Próximos Passos` é log append-only**: item concluído fica ~~riscado~~ com o
  resultado numérico anexado (contagem de testes, cobertura, nome da migration) e o número
  do PR. Não se apaga item, e por isso o documento também serve de histórico.
- **Achado negativo ganha seção com título próprio** (`## 2. Achado: middleware.ts está
  depreciado nesta versão`), nunca uma nota de rodapé.
- **`⚠️` marca o que fica com o usuário** — pré-requisito manual, credencial a criar,
  migration a aplicar no banco real.
- Links relativos entre documentos, `[[wikilinks]]` para conceitos, linkagem densa na
  primeira menção.
- **Commits**: Conventional Commits em português com **escopo de etapa** —
  `feat(fase2-e10):`, `docs(fase2-e9b):`, `fix(etapa11):`. Sufixo `(Qn)` quando o commit
  implementa a resposta da pergunta numerada `n` feita ao usuário naquela sessão.

## Aplicação

Esta cadeia é plantada pela skill `second-brain-sync` (Behavior 4 — Project Definition
Bootstrap), sempre perguntando antes de escrever. Os esqueletos vazios estão em
`90_Assets/Template_PRD.md`, `Template_RFC-000-Visao-de-Fase.md`, `Template_RFC.md`,
`Template_Plano-de-Fase.md`, `Template_Nota-de-Etapa.md`, `Template_Playbook.md` e
`Template_Prompt-de-Sessao.md`.

O que se replica é a **estrutura e a rastreabilidade**, nunca o conteúdo: a instância do
`orbita-platform` é Next.js/Prisma/Docker e não deve ser copiada literalmente para projeto
de outra stack — mesmo cuidado que o [[Checklist de Bootstrap de Workflow de Desenvolvimento]]
exige com a instância Java/Tycho de onde ele veio.

## 🔗 Conexões
- [[PRD]]
- [[RFC de Produto - Anatomia e Ciclo de Status]]
- [[Plano de Fase em Etapas Mescláveis]]
- [[Nota de Conclusão de Etapa é Entregável, Não Relatório]]
- [[Playbook de Projeto - Erros Já Cometidos Como Artefato]]
- [[Checklist de Bootstrap de Workflow de Desenvolvimento]]
- [[Padrão de Documentação Agêntica Local]]
- [[Documentação Desatualizada é Bug, Não Dívida]]
- [[Engenharia de Sistemas Agêntica]]
- [[Aplicação das Fases SE em Software Agêntico]]
