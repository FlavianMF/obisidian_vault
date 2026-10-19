---
title: Supabase CLI em CI - link por Pooler, db push sem Seed e Staging Tem que Ser Projeto Novo
type: trap
tags: [supabase, supabase-cli, migrations, db-push, ci-runner]
created: 2026-10-19
provenance: outlet_promo
project: outlet_promo
seen_in: [outlet_promo]
verified: 2026-10-19 via `supabase ... --help` da CLI 2.119.0 e docs.supabase.com (managing-environments) no plano da fase 6 do outlet_promo; deploy em CI ainda não executado
confidence: low
scope: global
---

# Supabase CLI em CI - link por Pooler, db push sem Seed e Staging Tem que Ser Projeto Novo

Versão de referência: Supabase CLI **2.119.0** (reverifique o `--help` ao atualizar).

## Sequência no workflow de deploy

`supabase link --project-ref "$REF"` › `supabase migration list` › `supabase db push --dry-run` ›
`supabase db push --yes` › `supabase secrets set ...` › `supabase functions deploy <fn> --use-api`.
Env: `SUPABASE_ACCESS_TOKEN` e `SUPABASE_DB_PASSWORD`. **Faça o build do app antes**, para falhar
antes de tocar no remoto.

## Armadilhas

- **`link` usa o pooler por padrão** (IPv4). O runner do GitHub não tem IPv6, então não use
  `--skip-pooler`.
- **`db push` NÃO roda `seed.sql`**. Dado de núcleo (que o app exige em produção) tem que estar
  em **migration**; o seed é só para dev local.
- **`--yes` é flag global**; `db push --dry-run` mostra o que seria aplicado.
- **`functions deploy --use-api` empacota sem Docker** (sem a flag, o bundle usa o Docker do
  runner). Se a função tiver `deno.json` que o empacotador API não entenda, volte ao modo Docker.
- **Staging precisa ser projeto novo.** SQL manual no Dashboard gera *drift* e o `db push`
  recusa; recuperação: `supabase migration repair`. Em projeto novo o `db push` cria o histórico e
  aplica tudo em ordem.
- **Token pessoal (`SUPABASE_ACCESS_TOKEN`) dá acesso à conta inteira**: só nos Environments
  `staging` e `prod`, nunca no de preview de PR.
- **SMTP padrão do Supabase hospedado só envia e-mail para membros do time**: convites e
  recuperação de senha para outros endereços falham até configurar SMTP próprio.
- Projeto novo pode vir sem as chaves legadas (`anon`/`service_role`): confira no setup se o
  código lê as chaves que o ambiente realmente injeta.

## Bootstrap remoto sem `psql` local

Quando a imagem de dev não tem `psql` (ex.: criar o primeiro admin), rode o cliente de dentro da
imagem do Postgres da Supabase, com a senha digitada no prompt (nunca na linha de comando):

```bash
docker run --rm -it --entrypoint psql public.ecr.aws/supabase/postgres:<tag> \
  "host=<session-pooler> ... sslmode=require"
```

## O que NÃO funcionou

Nada executado ainda em CI. O plano evita por leitura de doc/`--help`: `link` direto ao banco
(IPv6), esperar seed no `db push`, e preparar staging com SQL manual.

## Conexões
- [[Reusar CI como Portão de Deploy com workflow_call, Não workflow_run]]
- [[Gate de Produção em Repo Privado GitHub Free - Sem Required Reviewers, Release Mais workflow_dispatch com verify]]
