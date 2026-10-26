---
title: Preview de PR Aponta para o Staging sem as Migrations da PR - PGRST106 em api_v1 Quebra o Login até o Merge
type: trap
tags: [supabase, postgrest, ci, preview-channel, firebase-hosting, deploy]
created: 2026-10-26
provenance: outlet_promo
project: outlet_promo
seen_in: [outlet_promo]
verified: 2026-10-26 via login do painel no preview da PR #20, smoke de superfície da API contra o staging e rerun do deploy
confidence: low
scope: global
---

# Preview de PR Aponta para o Staging sem as Migrations da PR - PGRST106 em api_v1 Quebra o Login até o Merge

## Sintoma

O preview de uma PR carrega o painel, o login por link mágico funciona (`POST /auth/v1/token` devolve 200) e a chamada seguinte falha:

- `POST /rest/v1/rpc/get_my_staff_role` devolve 406.
- O corpo diz `PGRST106`, "Invalid schema: api_v1", "Only the following schemas are exposed: public, graphql_public".
- O app mostra "Não foi possível verificar seu acesso. Confira a conexão e tente de novo." A mensagem culpa a rede e esconde a causa.

## Causa

O preview publica só o front-end da PR no Hosting. Ele aponta para o Supabase de `staging`.

As migrations e a exposição do schema só rodam no deploy de `staging`, que dispara no push para `develop`. Enquanto a PR não entra em `develop`, o `staging` não tem o schema novo exposto. O front-end da PR chama um schema que o backend ainda não serve.

O erro 406 em `rpc/*` com `PGRST106` quer dizer "schema fora da lista exposta". Ele não indica bug no código de login.

## Como confirmar rápido

1. Abra a aba de rede e leia o corpo do 406. O código `PGRST106` fecha o diagnóstico.
2. Pergunte se a PR traz migration ou mudança de schema exposto que ainda não foi para `develop`.
3. Teste o login em `staging` depois do merge, não no preview.

## Segunda armadilha: o smoke logo depois do PATCH do Data API

No deploy que mergeou a PR, o passo do smoke falhou depois de `PATCH /v1/projects/{ref}/postgrest` com `db_schema = api_v1`:

- O `GET` da Management API já devolvia `api_v1`.
- O PostgREST hospedado ainda aceitava `public`: um `GET` com `Accept-Profile: public` devolvia 401 com `42501`, e não 406.
- Uma view de `api_v1` sem cabeçalho de perfil devolvia 404.
- Uma chamada com `Accept-Profile: api_v1` já respondia 200.

Um rerun do deploy, alguns minutos depois, passou, e o login voltou a funcionar. A causa mais provável é atraso na recarga do PostgREST depois do PATCH. Isso não foi provado: o script tentava 10 vezes com 3 segundos de intervalo, cerca de 30 segundos.

## Diagnóstico quando o log do GitHub não abre

`gh run view <id> --log-failed` pode devolver `503 Egress is over the account limit`. Alternativa que funcionou:

- Veja qual passo falhou com `gh run view <id> --json jobs`.
- Rode o mesmo smoke localmente. Leia a URL e a chave anon das variáveis do ambiente com `gh variable get SUPABASE_URL --env staging` e `gh variable get SUPABASE_ANON_KEY --env staging`. Não imprima a chave.

## O que NÃO funcionou

- Ler o log do job com `--log-failed`: bloqueado pelo limite de egress.
- Tratar o preview como prova de bug de login: o código de login estava certo, o backend é que estava atrasado.
- Confiar em 30 segundos de retry depois do PATCH do Data API: o smoke falhou nessa janela e passou no rerun.

## Como evitar

- Avise na descrição da PR: "o preview só loga depois do merge em `develop`".
- Aumente as tentativas do smoke pós-PATCH, ou espere o schema aparecer antes de checar o 406.
- Mostre no app o motivo real do erro: separe link expirado, falta de permissão e falha de API.
