---
title: develop é Staging, master é Prod - verify Exige Merge Commit com Staging Verde
type: decision
tags: [ci-cd, github-actions, deploy, staging, outlet_promo]
created: 2026-10-22
provenance: outlet_promo
seen_in: [outlet_promo]
confidence: low
scope: global
verified: 2026-10-22 via candidato do agente em outlet_promo, não reproduzido na revisão
---

# develop é Staging, master é Prod - verify Exige Merge Commit com Staging Verde

## Decisão

`develop` é staging e `master` é produção. O **merge de `develop` em `master` é a única aprovação** de produção.

## Como funciona

- O job `verify` confere o **segundo pai** do commit de `master` (ou o SHA) e exige um job de staging com `success` em `deploy-staging.yml`. O run pode estar vermelho por causa do job de iOS; o que conta é o job de staging.
- **Squash e rebase falham:** o `verify` pede "Create a merge commit".
- `ci` e `db` rodam **só via `workflow_call`** dentro do deploy, sem `push` próprio, para não rodar em dobro.

## O que NÃO funcionou

Squash ou rebase do `develop` em `master`: o `verify` não acha o segundo pai e recusa.

## Relacionadas

- [[Reusar CI como Portão de Deploy com workflow_call, Não workflow_run]]
- [[Gate de Produção em Repo Privado GitHub Free - Sem Required Reviewers, Release Mais workflow_dispatch com verify]]
