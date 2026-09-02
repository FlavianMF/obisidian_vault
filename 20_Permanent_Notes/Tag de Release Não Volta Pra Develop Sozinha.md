---
title: Tag de Release Não Volta Pra Develop Sozinha
type: trap
tags: [git, release, versioning, ci-cd, tags, dev-workflow]
created: 2026-09-02
provenance: capella_llm_window
project: capella_llm_window
---

# Tag de Release Não Volta Pra Develop Sozinha

## Contexto

Fluxo de release comum: trabalho entra em `develop` via PR, quando pronto
abre-se PR `develop` → `master`, e um workflow de CI (`tag-release.yml` no
capella_llm_window) lê a versão do build e cria a tag (`vX.Y.Z`) **em
cima de `master`** depois desse merge. Nada nesse fluxo mergeia `master`
de volta em `develop`.

Consequência: a tag existe só na ancestralidade de `master`. Qualquer
branch cortada de `develop` depois disso não tem a tag como ancestral —
`git describe --tags` (ou qualquer ferramenta que dependa de
alcançabilidade de tag, como `git-commit-id-maven-plugin`'s
`git.commit.id.describe`) reporta a tag **anterior** mais contagem de
commits, não a atual, mesmo que outros campos de versão (ex.: um
`Bundle-Version` lido direto de um manifest/arquivo) já estejam corretos.

Descoberto construindo um fallback de dev-mode pro comando `/version` de
um plugin Eclipse: `Bundle-Version` lido do MANIFEST.MF batia `0.0.3`
certo, mas `git describe` numa branch cortada de `develop` mostrava
`v0.0.2-21-g<hash>`. Confirmado com
`git merge-base --is-ancestor v0.0.3 HEAD` → não era ancestral.

## Padrão

Depois de qualquer release que tageia só uma branch "de cima" (`master`,
`main`, `release`), a branch "de baixo" (`develop`) fica com um gap de
alcançabilidade de tag até alguém mergear de volta — mesmo que o conteúdo
seja idêntico (back-merge nesse caso costuma ser diff vazio, só sincroniza
histórico). Corrigir fazendo merge de `master` em `develop` (local, sem
conflito esperado se o conteúdo já é igual) e dando push.

## Quando aplicar

- Diagnosticando "versão errada mostrada" que envolve `git describe`,
  `git.commit.id.describe`, ou qualquer string de versão baseada em tag —
  verificar `git merge-base --is-ancestor <tag> HEAD` antes de assumir bug
  de código.
- Ao desenhar/revisar um pipeline de release com branch de
  desenvolvimento + branch de release separadas: considerar automatizar o
  back-merge como último passo do workflow de tag, em vez de depender de
  alguém lembrar manualmente a cada ciclo.

## 🔗 Conexões
- [[Confirmar Qual Worktree Está Sendo Testada Antes de Diagnosticar]]
