---
title: Escopo de Trigger de CI - push Só nas Branches Protegidas, pull_request Cobre o Resto
type: pattern
tags: [github-actions, ci-cd, developer-experience]
created: 2026-09-02
provenance: capella_llm_window
project: capella_llm_window
---

# Escopo de Trigger de CI - push Só nas Branches Protegidas, pull_request Cobre o Resto

## Problema

`on: push:` sem filtro de branch dispara o CI inteiro a cada push, em
qualquer branch — inclusive branches de feature/fix em WIP, antes de
existir PR nenhum, às vezes vários pushes seguidos enquanto alguém ainda
tá iterando localmente. Gasta minuto de CI (relevante em runners pagos)
sem ganhar sinal nenhum a mais, já que ninguém tá olhando esse resultado
ainda.

## Padrão

```yaml
on:
  push:
    branches: [main, develop]   # só as branches de vida longa/protegidas
  pull_request:                  # sem filtro de branch - cobre feature/fix
```

`push:` só nas branches protegidas (as que recebem merge direto e
importam sempre ter CI verde — `main`/`master`, `develop`, etc.).
Branches de feature/fix não ganham push-trigger próprio: dependem
inteiramente do evento `pull_request`, que já reroda a cada
`synchronize` (novo commit) uma vez que o PR existe. Resultado: zero
perda de cobertura de CI pra qualquer coisa que vai virar PR (que é toda
mudança de verdade), zero desperdício em pushes de branch sem PR aberto
ainda.

## Quando aplicar

Qualquer repo GitHub Actions onde o fluxo padrão é "toda mudança de
verdade passa por PR" (praticamente todo fluxo com branch protection).
Não serve pra fluxos que dependem de push direto em branches de feature
sem PR como sinal em si (raro, geralmente só em repos pessoais/sem
colaboração).

Exemplo real: `.github/workflows/ci.yml` em `capella_llm_window`,
`on: push: branches: [master, develop]` + `pull_request:` sem filtro.

## 🔗 Conexões
- [[Gate de Cobertura Tem Que Excluir do Numerador E do Denominador, Não Só Relaxar o Limiar]]
