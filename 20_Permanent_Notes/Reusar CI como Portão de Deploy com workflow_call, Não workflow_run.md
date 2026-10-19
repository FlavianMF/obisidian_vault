---
title: Reusar CI como Portão de Deploy com workflow_call, Não workflow_run
type: pattern
tags: [github-actions, reusable-workflows, concurrency, deploy-pipeline]
created: 2026-10-19
provenance: outlet_promo
project: outlet_promo
seen_in: [outlet_promo]
verified: 2026-10-19 via plano da fase 6 do outlet_promo (Tasks 11 e 13, nota final); workflows ainda não executados
confidence: low
scope: global
---

# Reusar CI como Portão de Deploy com workflow_call, Não workflow_run

## Problema

O deploy de staging só pode sair se `ci.yml` **e** `db.yml` estiverem verdes **no mesmo SHA**.
`workflow_run` dispara uma vez por workflow observado e não junta resultados, então cada um
acionaria um deploy ou nenhum.

## Padrão

1. `ci.yml` e `db.yml` ganham `on: workflow_call:` além dos gatilhos atuais.
2. O workflow de deploy os chama como jobs (`uses: ./.github/workflows/ci.yml`, `permissions:
   contents: read`) e o job de deploy declara `needs: [ci, db]`. Etapas independentes do deploy
   (ex.: build iOS) ficam fora do `needs` se não devem segurá-lo.
3. **Tire a branch de deploy do `push` dos workflows reutilizados** (`push.branches: [develop]`,
   sai `master`). Dois motivos: não rodar tudo em dobro e, no `ci.yml`, impedir que o
   `cancel-in-progress: true` do mesmo grupo cancele a validação chamada pelo deploy.
4. `concurrency.cancel-in-progress: ${{ github.event_name == 'pull_request' }}`: só PR cancela
   run antigo; push e chamada de deploy nunca.
5. Workflow de deploy reutilizável (`_deploy-env.yml`, `on: workflow_call` com inputs
   `environment` e `ref`): o job que declara `environment:` lê os **secrets do Environment
   direto**. Secrets de Environment **não passam pelo caller**, então não tente repassá-los por
   `secrets:`. `concurrency: deploy-<env>` com `cancel-in-progress: false`.

## Relação com a nota de trigger

Refina [[Escopo de Trigger de CI - push Só nas Branches Protegidas, pull_request Cobre o Resto]]:
`push` nas branches protegidas continua valendo, exceto na branch cujo push já dispara o deploy
(que chama o CI por `workflow_call`).

## O que NÃO funcionou

Nada rodou ainda. Descartado por raciocínio: `workflow_run` (não agrega os resultados de dois
workflows no mesmo SHA); manter `master` no `push` dos dois workflows (execução dobrada e risco de
cancelamento cruzado).

## Conexões
- [[Escopo de Trigger de CI - push Só nas Branches Protegidas, pull_request Cobre o Resto]]
- [[Gate de Produção em Repo Privado GitHub Free - Sem Required Reviewers, Release Mais workflow_dispatch com verify]]
