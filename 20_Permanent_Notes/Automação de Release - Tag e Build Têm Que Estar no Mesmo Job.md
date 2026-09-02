---
title: Automação de Release - Tag e Build Têm Que Estar no Mesmo Job
type: pattern
tags: [github-actions, ci-cd, release-automation, git]
created: 2026-09-02
provenance: capella_llm_window
project: capella_llm_window
---

# Automação de Release - Tag e Build Têm Que Estar no Mesmo Job

## Problema

Desenho "óbvio" de automação de release: um workflow A cria/empurra a
tag `vX.Y.Z` quando a versão muda na branch de release; um workflow B,
acionado por `push: tags: ['v*']`, faz o build e publica a GitHub
Release. Parece limpo (responsabilidade separada), mas **nunca dispara
na prática**: um tag/commit empurrado usando o `GITHUB_TOKEN` padrão do
próprio job **não aciona outros workflows** — salvaguarda anti-recursão
deliberada do GitHub Actions (documentada, não é bug). O workflow A roda
e "funciona" (a tag aparece no repo), mas o workflow B nunca é chamado —
sintoma: tag existe, sem Release nenhuma anexada, sem nenhum erro visível
em lugar nenhum.

## Padrão

Um workflow só, acionado direto pelo evento de push na branch de release
(não pela tag em si):

1. Lê a versão de onde o projeto a declara (manifest, `package.json`,
   `Cargo.toml`, `pyproject.toml`, etc. — qualquer fonte única de
   verdade).
2. Confere se a tag `vX.Y.Z` correspondente já existe (`git rev-parse
   "$TAG"`) — se sim, **não faz nada** (idempotente: evita re-lançar a
   mesma versão sem querer num push que não bumpou a versão). Se não,
   cria e empurra a tag.
3. **No mesmo job**, condicionado a "a tag era mesmo nova" (via
   `steps.<id>.outputs.created`/equivalente): build, testes, empacotar,
   publicar a Release — sem esperar outro workflow, sem trigger
   encadeado nenhum.

Alternativa que também funciona (não usada aqui, mas válida): usar um PAT
ou GitHub App token em vez do `GITHUB_TOKEN` padrão pra empurrar a tag —
tokens que não são o `GITHUB_TOKEN` de job *conseguem* disparar outros
workflows. O padrão de job único evita precisar gerenciar esse segredo
extra.

## Quando aplicar

Qualquer pipeline de release no GitHub Actions que hoje depende de "tag
dispara outro workflow" — Node, Python, Rust, Go, qualquer stack. O
sintoma (tag criada, nada mais acontece, sem erro) é o sinal de que caiu
nessa pegadinha. Exemplo real:
`.github/workflows/tag-release.yml` em `capella_llm_window` — o próprio
comentário no topo do arquivo documenta a migração de dois workflows
encadeados pra um só, depois do primeiro release real não ter publicado
nada.

## 🔗 Conexões
- [[Gate de Cobertura Tem Que Excluir do Numerador E do Denominador, Não Só Relaxar o Limiar]]
