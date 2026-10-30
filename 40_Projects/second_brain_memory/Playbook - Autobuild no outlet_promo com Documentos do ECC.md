---
title: Playbook - Autobuild no outlet_promo com Documentos do ECC
type: project
tags: [agentic-ai, traycer, evaluation, flutter, ecc]
created: 2026-10-29
provenance: manual
project: outlet_promo
verified: 2026-10-29 via leitura do repo `/home/flv/projetos_apps/outlet_promo` e do plugin `ecc@ecc` 2.2.2
confidence: low
status: active
---

# Playbook - Autobuild no outlet_promo com Documentos do ECC

Aplica o método de [[Autobuild - Loop Adversarial Generator Evaluator com Contrato e Rubrica]] ao `outlet_promo`. Nada daqui foi executado. É um plano.

## Estado do projeto (2026-10-29)

- Monorepo Flutter (`apps/consumer`, `apps/admin`, `packages/core`) com Supabase, Firebase Hosting e PWA.
- Fluxo local: `make check`, `make test`, `make format`, `make analyze`. Os testes têm 79 arquivos Dart e pgTAP em `supabase/tests/`.
- Guardas prontos em `tool/`: `check_client_writes.sh`, `check_api_surface.sh`, `check_coverage.sh` (mínimo 80% no core), `check_l10n.sh`, `check_theme_usage.sh`, `check_platform_usage.sh`.
- Spec pronta: `docs/prds/*.prd.md` e `docs/plans/`. Use-os no lugar de gerar uma spec nova.
- Falta `CLAUDE.md` e `AGENTS.md` na raiz. Crie um antes do build, com comandos, convenções e a regra `.claude/rules/ecc-artifacts.md`.

## Mapa ECC para papéis do autobuild

`$E` = `~/.claude/plugins/cache/ecc/ecc/2.2.2`.

| Peça do autobuild | Documento ECC | Uso |
| --- | --- | --- |
| Spec do Planner | `$E/agents/gan-planner.md`, `$E/docs/PLAN-PRD-PATTERN.md` | Molde de sprints. A spec real vem de `docs/prds/`. |
| Loop do Generator | `$E/agents/gan-generator.md`, `$E/skills/tdd-workflow/SKILL.md` | Regra de testes primeiro. |
| Relatório do Evaluator | `$E/agents/gan-evaluator.md` | Tabela de notas e feedback acionável. Troque o Playwright pelo caminho de avaliação do projeto. |
| Layout da rubrica | `$E/examples/gan-harness` (`eval-rubric.md`) | Modelo de arquivo. |
| Contrato como evals | `$E/skills/eval-harness/SKILL.md` | Graders por código, pass@k e pass^k. |
| Caminho de avaliação | `$E/skills/verification-loop/SKILL.md` | Base da sequência build, lint, teste, segurança, diff. |
| Inegociável de segredo | `$E/skills/security-review/SKILL.md`, `$E/rules/common/security.md` | Checklist de segredos e entrada. |
| Critério de banco | `$E/agents/database-reviewer.md`, `$E/skills/postgres-patterns/SKILL.md` | RLS, migrations, índices. |
| Critério Dart | `$E/rules/dart/*.md`, `$E/agents/flutter-reviewer.md`, `$E/skills/flutter-dart-code-review/SKILL.md` | Estilo, teste e revisão. As rules `dart/` valem só se você citá-las. |
| Controle de loop e orçamento | `$E/agents/loop-operator.md`, `$E/skills/context-budget`, `$E/skills/token-budget-advisor` | Tetos e custo. |

## O que escrever do zero

O ECC dá nota única (escala 1 a 10, limiar 7,0). Ele não tem contrato negociado nem veredito duplo. Escreva estes itens:

1. **Inegociáveis.** Candidatos:
   - Nenhuma escrita direta do cliente no PostgREST (`tool/check_client_writes.sh`).
   - RLS ligada em toda tabela (`supabase/tests/00_rls_enabled.test.sql`).
   - Nenhum segredo nem PII em log, commit ou PR.
   - Nenhuma asserção existente removida ou afrouxada.
2. **Critérios com peso.** Pese bordas, força dos testes, i18n pt/en/es, tokens do `DESIGN.md` e fluxo de auth e lead.
3. **Caminho de avaliação.** O Evaluator precisa rodar `make check`, pgTAP e `tool/check_*.sh` via Docker. Meça a contagem de linha de base antes do lançamento. O Evaluator do ECC assume app web com Playwright e não cobre Flutter nem Supabase.
4. **Ambiente isolado.** Um worktree por build e `EV=$(mktemp -d)`. Proíba o Evaluator de tocar em `.env*`, no Supabase real e nos deploys.
5. **Tetos.** Use 4 trocas de contrato, 3 rodadas, 1 restart. Peça relançamento perto de 160k tokens totais.

## Passos

1. Escolha o escopo: um PRD ou uma fase de `docs/prds/`.
2. Crie `CLAUDE.md` e `AGENTS.md` no `outlet_promo`.
3. Escreva spec, rubrica e caminho de avaliação como artifacts do épico.
4. Rode as suítes e registre a linha de base.
5. Cheque a cota do `claude` e lance Generator sonnet e Evaluator opus.
6. Confira os worktrees ativos em `/home/flv/.traycer/worktrees/flavianmf__outlet_promo/`. Eles não podem colidir com o novo build.
7. Pare antes do merge. O usuário revisa e faz o squash.

## O que NÃO funcionou

Nada foi executado no `outlet_promo`. O autobuild só foi testado com CLI e testes, sem browser. Se o Evaluator precisar de browser, um MCP de browser chamável no harness dele ainda não foi exercitado.
