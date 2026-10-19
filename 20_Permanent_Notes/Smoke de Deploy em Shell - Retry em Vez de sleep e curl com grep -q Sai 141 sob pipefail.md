---
title: Smoke de Deploy em Shell - Retry em Vez de sleep e curl com grep -q Sai 141 sob pipefail
type: trap
tags: [bash, pipefail, smoke-test, curl, deploy-verification]
created: 2026-10-19
provenance: orbita-platform
project: orbita-platform
seen_in: [orbita-platform]
verified: 2026-10-19 via deploy-producao.yml e deploy-homologacao.yml do orbita-platform (comentário no código) e CI-CD-Pipeline.md §5.4; reaproveitado no plano da fase 6 do outlet_promo (tool/check_hosting.sh), ainda não executado lá
confidence: low
scope: global
---

# Smoke de Deploy em Shell - Retry em Vez de sleep e curl com grep -q Sai 141 sob pipefail

## Armadilha 1: `curl | grep -q` com `pipefail` dá falso negativo

Num script com `set -o pipefail` (ou `set -euo pipefail`), `curl -s URL | grep -q marcador` falha
mesmo com o marcador presente: o `grep -q` encontra e sai na hora, fecha o pipe, o `curl` leva
SIGPIPE e sai com **141**. O deploy cai por um erro que não existe.

Padrão correto: ler o corpo para uma variável e testar com `case`, sem pipe.

```bash
check_area() {
  wait_for "$1" || return 1
  local body
  body=$(curl -sf "$1") || { echo "$1 nao respondeu ao ler o corpo" >&2; return 1; }
  case "$body" in
    *"$2"*) echo "$1 area OK ($2)" ;;
    *) echo "$1 respondeu, mas NAO serve a area esperada ($2)" >&2; return 1 ;;
  esac
}
```

Para provar roteamento (e não só "a porta responde"), procure um marcador estável do **seu
código** (ex.: `metadata.title` de um layout), não um header interno do framework.

## Armadilha 2: `sleep` fixo + uma tentativa

`sleep 5` seguido de um único `curl` falhou no primeiro deploy real de produção (curl exit 56,
`RECV_ERROR`): o container rodava `next dev`, que compila cada rota na primeira requisição, e a
rota fria levou mais de 1 min. Os containers já estavam no ar; só o smoke derrubava o workflow.
Use retry com teto:

```bash
wait_for() {
  for i in $(seq 1 30); do
    curl -sf -o /dev/null "$1" && { echo "$1 OK"; return 0; }
    sleep 3
  done
  echo "$1 FAILED apos 90s" >&2
  return 1
}
```

Num script testável, injete o `SLEEP` (ou o intervalo) para o teste não esperar de verdade.

## O que NÃO funcionou

- `sleep 5` fixo mais tentativa única de `curl` (falhou no deploy real de produção do orbita).
- `curl | grep -q` sob `pipefail` (exit 141); o orbita registrou o motivo em comentário no
  próprio workflow, ao lado do `case`.

## Conexões
- [[Firebase Hosting no GitHub Actions - action-hosting-deploy e firebase.json Têm Armadilhas]]
