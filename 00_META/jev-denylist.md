---
title: Jev denylist
type: meta
created: 2026-10-05
---

# Jev denylist

Notas e repos que nunca saem da máquina para a API TypeSafe (estudo `jev_second_brain`).
Arquivo ausente, ilegível ou sem regras = nada é enviado (fail-closed).

Formato: uma regra por linha, `- folder|tag|repo|term: valor`.

- `folder`: prefixo do caminho da nota (ex.: `40_Projects/fit/`)
- `tag`: tag exata, sem diferenciar maiúsculas
- `repo`: nome do repo; o prompt de sessões nesse repo não é enviado
- `term`: palavra procurada em provenance, seen_in, tags, caminho e nome do repo, com fronteira de letra

As tags `private`, `privado`, `pessoal`, `personal`, `sensitive` e `confidential` são sempre bloqueadas.

<!-- Sugestão inicial herdada de jev-workflow (DEFAULT_EXCLUDE_MARKER_TERMS). Revisar antes do sync. -->

- term: pnaat
- term: mestrado
- term: cariri
- term: bel
- term: projetos_ita
- term: conops
