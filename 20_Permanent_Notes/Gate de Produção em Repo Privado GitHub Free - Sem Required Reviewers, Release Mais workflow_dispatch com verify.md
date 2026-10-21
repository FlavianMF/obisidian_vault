---
title: Gate de Produção em Repo Privado GitHub Free - Sem Required Reviewers, Release Mais workflow_dispatch com verify
type: trap
tags: [github, environments, branch-protection, release-gate, workflow-dispatch, semver]
created: 2026-10-19
provenance: outlet_promo
project: outlet_promo
seen_in: [orbita-platform, outlet_promo]
verified: 2026-10-21 via run 39619762122 do outlet_promo (PR #10 develop→master, merge commit, v0.0.1 em prod); antes 2026-10-19 via CI-CD-Pipeline.md do orbita-platform
confidence: high
scope: global
---

# Gate de Produção em Repo Privado GitHub Free - Sem Required Reviewers, Release Mais workflow_dispatch com verify

## Armadilha

Em **repositório privado no plano Free**, as travas nativas de aprovação não existem, e a API diz
isso de forma explícita (confirmado no `orbita-platform`, org Free, 2026-07-22):

| Tentativa | Resposta |
|---|---|
| `PUT repos/<r>/environments/<env>` com `reviewers: [...]` | `422 Failed to create the environment protection rule. Please ensure the billing plan supports the required reviewers protection rule` |
| `gh api repos/<r>/branches/<b>/protection` | `403 Upgrade to GitHub Pro or make this repository public to enable this feature` |

Pela doc do GitHub (deployments and environments):

- **Required reviewers e wait timer**: só repo público (ou Enterprise); Free, Pro e Team **não** em
  privado.
- **Environment secrets**: a doc diz que no Free só valem em repo público. No `orbita-platform`
  (organização Free, repo privado) Environments com secrets **funcionaram**. Em Pro/Team valem em
  privado, junto com "deployment branches and tags".
- A API REST **não tem endpoint para renomear** Environment: errou o nome, apague e recrie e
  reinsira os secrets.

## O que fazer em vez disso (origem: orbita-platform §9; adotado no outlet_promo, D1)

Duas ações humanas deliberadas substituem a aprovação paga:

1. Validar em homologação/staging (o merge na branch de integração já publicou lá sozinho).
2. Cortar a Release **de `master`**: `gh release create vX.Y.Z --target master --generate-notes`.
   Publicar a Release **não** faz deploy de produção.
3. Actions › workflow de prod › *Run workflow* com a **tag como input obrigatório**
   (`on: workflow_dispatch`, sem gatilho de push nem de `release`).
4. `environment: prod` fica declarado no job **só para escopar secrets**. Se o plano mudar, basta
   pôr o reviewer nas Settings: nenhuma mudança de código.

### Reforço do outlet_promo: job `verify` antes do deploy

Falha se qualquer item for falso:

- `github.ref` é `refs/heads/master`;
- a tag casa `^v[0-9]+\.[0-9]+\.[0-9]+$` e existe (`git ls-remote --tags`);
- o commit da tag está em `master` (`git merge-base --is-ancestor`, checkout com `fetch-depth: 0`);
- o commit tem run `success` do workflow de staging:
  `gh api "repos/$REPO/actions/workflows/deploy-staging.yml/runs?head_sha=$SHA&status=success"`.

Saídas `sha` e `build-name` (tag sem o `v`) alimentam o job de deploy. Prod só recebe o que já
passou por staging.

### Limite do desenho

Sem reviewer, a trava técnica é fraca: quem dispara de **outra branch roda o arquivo de workflow
daquela branch**, inclusive um `verify` editado. A proteção real seria a regra de branch do
Environment (só `master`), que depende do plano; se indisponível, registre no README e trate
como disciplina.

## O que NÃO funcionou

- Required reviewers no Environment (422) e branch protection em `develop` (403): no orbita
  sobrou disciplina manual (só mesclar PR com CI verde).
- Renomear o Environment `Staging`, criado por engano, para `production`: sem API; foi preciso
  apagar e recriar com os 6 secrets.
- O fluxo Release + dispatch opera no orbita desde 2026-07-22; o `verify` é desenho do
  outlet_promo, ainda não executado (devem falhar: tag inexistente, fora do padrão, ou não
  publicada em staging).

## Confirmado no outlet_promo (2026-10-21, primeiro lançamento, v0.0.1)

- Environment com secrets funciona em repo privado de organização no plano Free; `gh secret list --env prod` e `gh variable list --env prod` conferem antes do PR.
- Com "Create a merge commit", `verify` passou, `version` criou a tag e a Release `v0.0.1` e `prod` publicou no mesmo run. A tag aponta para o SHA do merge em `master`.
- Se `prod` falha depois de `version`, tag e Release já existem. `gh run rerun <id> --failed` refaz só o job vermelho e reaproveita a mesma versão; não apague a tag.
- `ci` e `db` rodam também no evento `pull_request` do PR `develop`→`master` (não só no deploy), mas o preview não dispara.
- `gh variable list` imprime os valores das vars; `gh secret list` não. Para "conferir nomes", use `| cut -f1`.
- Falha do smoke logo após o deploy: ver [[Firebase Hosting no GitHub Actions - action-hosting-deploy e firebase.json Têm Armadilhas]].

## Conexões
- [[Automação de Release - Tag e Build Têm Que Estar no Mesmo Job]]
- [[Tag de Release Não Volta Pra Develop Sozinha]]
- [[Reusar CI como Portão de Deploy com workflow_call, Não workflow_run]]
