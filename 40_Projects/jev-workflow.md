---
title: Projeto jev-workflow
type: project
tags: [project, agentic-ai, claude-code, jev, typesafe, hooks]
created: 2026-09-30
provenance: jev-workflow
seen_in: [jev-workflow]
confidence: low
verified: 2026-09-30 via gh repo create e leitura do plano
status: active
scope: project
---

# Projeto jev-workflow

Nota-ponteiro. O plano completo vive no repo, não aqui.

- Repo (privado): https://github.com/FlavianMF/jev-workflow
- Plano: `docs/PLANO.md` no repo (cópia de `PLANO-JEV.md`, 2026-09-30)
- Local: `~/projetos_claude/jev-workflow`

## Objetivo

Seis ferramentas pequenas que usam o modelo Jev (TypeSafe, "System One": perguntas tipadas noul/choice/score, sem geração de texto) no workflow de desenvolvimento com Claude Code: **E** sugestor de skill, **D** portão consultivo de risco para Bash, **B** matcher de duplicata de notas, **C** rerank do `session_hint`, **H1** triagem de commit por metadados, **I1** lint de afirmações de estado em notas. Domínio do Jev como subproduto.

## Prazo

O crédito de US$ 5 (dado do usuário) expira em **2026-10-20**. Coleta de dados com Jev antes disso; retrospectiva e decisão continuar/sunset em **2026-10-19** (regra: custo projetado <= US$ 1/mês, acordo >= 90%, ganho >= 10 pontos sobre a heurística atual em E ou D). Teto de gasto do plano: US$ 3,00, corte local a 80%.

## Decisões

- Privacidade: só metadados e comandos redigidos saem da máquina; nada de prompt cru, diff ou corpo de nota.
- Ferramentas, em ordem: E, D, B, C, H1, I1.
- Sombra primeiro; sempre fail-open; D no máximo `ask`, nunca `deny`; E só injeta uma linha de contexto.
- TypeScript compilado para JS; hooks chamam `node dist/cli.js`; wiring só em `~/dotfiles`.

## Estado

Etapas 0 (fundação) e 1 (cliente, cache, orçamento, kill-switch) em PR no repo. Ver o repo para o estado atual (esta nota não o acompanha).

## Conexões
- [[claude-code]]
