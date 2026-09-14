---
title: Plano de Fase em Etapas Mescláveis
type: pattern
tags: [project-planning, dev-workflow, worktree, acceptance-criteria, project-methodology]
created: 2026-09-11
provenance: orbita-platform
project: orbita-platform
---

# Plano de Fase em Etapas Mescláveis

Como transformar um conjunto de RFCs aprovadas em ordem de execução. Destilado da Fase 2 do
`orbita-platform`: 8 RFCs viraram 10 etapas (`E0`–`E10`), cada uma mesclável sozinha, cada
uma validada pelo usuário antes do merge. Peça 6 da
[[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]].

## Forma do documento

```
# Plano de Ação — <Fase>: <Tema>
**Data** · **Base**: RFCs [000]–[00N] · **Governança**: [Playbook], [Diretrizes de Testes]

parágrafo: quantas etapas, qual a régua de merge, o que é fundação e o que é produto

## Visão das etapas e dependências        diagrama ASCII
## E0 — <título> ✅ Concluído (data)
## E1 — …
## Estratégia de testes (transversal)
## Riscos operacionais desta sequência    tabela | Risco | Mitigação |
## Próximos Passos                        log append-only
```

O diagrama ASCII de dependências vale mais que a lista, porque mostra o que é paralelizável:

```
E0 Fundações ──► E1 Onboarding ──► E2 Vínculo ──► E3 Carteira ──► E4 CRM
 (infra+auth)                     (consentimento)     │
                                                      ├────────► E5 Recomendações
                                                      ├────────► E6 Relatórios
                                                      └────────► E7 White-label
                                                                       │
                                                      E9 Encerramento ◄─┘
```

## Anatomia da etapa

```markdown
## E5 — Recomendações e planos de alocação ✅ Concluído (2026-07-23)

**RFC**: [004 §4](…) · **Depende**: E3 · Nota de conclusão: [Fase2-E5-…](…) · Worktree: `worktree-fase2-e5-recomendacoes` (mesclado em `develop`)

1. Modelos `Recomendacao`/`PlanoAlocacao`; máquina de estados de status.
2. Editor do consultor: percentuais-alvo (soma = 100%) + gap contra a alocação real.
3. Lado do cliente: notificação, visualização, aceite/recusa com comentário.

**Aceite**: transições ilegais de status rejeitadas; validação de soma; cliente só vê as
recomendações dele; taxonomia só muta por ADMIN.
**Atenção (Playbook)**: converter coluna `String` em FK exige `migration.sql` escrita à mão
— o `prisma migrate dev` não gera o backfill.
```

Campos, e por que cada um existe:

- **RFC (com §)** — a etapa implementa uma seção específica, não uma RFC inteira. `RFC-004 §4`.
- **Depende** — a única coisa que define a ordem. O resto é paralelizável.
- **Worktree** — nome da branch, e o estado: `(mesclado em develop)` ou `(aguardando
  validação/merge do usuário)`.
- **Nota de conclusão** — preenchida quando a etapa fecha
  ([[Nota de Conclusão de Etapa é Entregável, Não Relatório]]).
- **Itens numerados** — as entregas, não as tarefas. De 2 a 4 por etapa; mais que isso é
  sinal de que a etapa precisa ser fatiada.
- **Aceite** — escrito **antes** da execução.
- **Atenção (Playbook)** — a armadilha conhecida que essa etapa vai encontrar, linkada ao
  [[Playbook de Projeto - Erros Já Cometidos Como Artefato]].

## Aceite é teste negativo, não checklist

O critério de aceite que funciona descreve **o que tem que falhar**:

- "o consultor vê apenas clientes com vínculo `ATIVO` — teste com `REVOGADO`"
- "transições ilegais de status rejeitadas"
- "código de consultor não-`ATIVO` se comporta como inexistente"
- "impossível gravar sem gerar registro de auditoria"

O que não serve: "CRUD funcionando", "tela pronta", "coberto por testes". São afirmações que
nenhuma execução reprova.

Em domínio com múltiplos tenants, **teste negativo de autorização em toda rota nova é
obrigatório** — vazamento entre tenants costuma ser o risco nº 1 da tabela de riscos, e
filtro `undefined` em ORM não nega acesso: ele devolve tudo.

## E0 é fundação, En é encerramento

- **`E0`** só mexe em infraestrutura e migração de identidade/schema, **sem mudança visível
  para o usuário final**. Isso a torna a etapa mais segura de mesclar primeiro e a única
  onde uma regressão é fácil de atribuir.
- **`En` (encerramento)** não é "finalizar": é uma etapa de verdade, com escopo próprio —
  segurança (hardening, isolamento, cifra de segredo), qualidade (validação de entrada na
  borda, lint como gate, cobertura agregada) e fecho (build de produção, backup/reset,
  seed de demonstração). No `orbita-platform` ela precisou ser fatiada duas vezes
  (`E9a`/`E9b`, depois `E10`) — encerramento é sistematicamente subestimado.

## Fatiar sob demanda é normal

`E8` virou `E8a`/`E8b`; `E9` virou `E9a`/`E9b`. O gatilho não é complexidade técnica: é
**tamanho do diff que o usuário vai validar**. O corte é registrado no plano, com o motivo e
com a ordem ("`E8b` só começa após o merge de `E8a`, para evitar conflito de migrations").

Renumerar etapas já publicadas, não. Sufixo de letra preserva todos os links existentes.

## Uma etapa, uma worktree, um PR, uma nota

Relação 1:1:1:1. A etapa se desenvolve numa `git worktree` dedicada
(branch `worktree-<escopo>`), nunca no checkout compartilhado — ver
[[Checklist de Bootstrap de Workflow de Desenvolvimento]] eixo 1 e
[[Confirmar Qual Worktree Está Sendo Testada Antes de Diagnosticar]].

**O agente não mescla.** Ele termina a etapa, roda a suíte completa mais o typecheck, escreve
a nota, e avisa que a worktree está pronta. O usuário valida — idealmente rodando o código da
worktree num slot de homologação com dados reais — e faz o PR e o merge. Foi preferência
explícita do usuário no `orbita-platform`, e virou a regra que mais evitou retrabalho:
código que o agente considerou pronto e que o usuário reprovou ao ver na tela.

## `## Próximos Passos` é log, não lista de tarefas

Item concluído fica ~~riscado~~ **com o resultado anexado**: contagem de testes, cobertura
final, nome da migration criada, número do PR. Nada é apagado. O resultado é que a seção
vira o histórico da fase, legível de cima a baixo, e débito adiado conscientemente
(`next build` empurrado de `E9b` para `E10`) fica visível em vez de virar surpresa.

## 🔗 Conexões
- [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]]
- [[RFC de Produto - Anatomia e Ciclo de Status]]
- [[Nota de Conclusão de Etapa é Entregável, Não Relatório]]
- [[Playbook de Projeto - Erros Já Cometidos Como Artefato]]
- [[Checklist de Bootstrap de Workflow de Desenvolvimento]]
- [[Skill - Fluxo de Trabalho de Feature Branch]]
- [[Confirmar Qual Worktree Está Sendo Testada Antes de Diagnosticar]]
