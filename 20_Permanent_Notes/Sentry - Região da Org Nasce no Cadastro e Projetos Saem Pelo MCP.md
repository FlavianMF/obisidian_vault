---
title: Sentry - Região da Org Nasce no Cadastro e Projetos Saem Pelo MCP
type: trap
tags: [sentry, observabilidade, lgpd, mcp, flutter]
created: 2026-10-21
provenance: outlet_promo
seen_in: [outlet_promo]
verified: 2026-10-21 via MCP find_organizations (regionUrl us.sentry.io) e create_project
confidence: low
---

# Sentry - Região da Org Nasce no Cadastro e Projetos Saem Pelo MCP

## Armadilha

A região de dados (US ou EU) é escolhida quando a organização é criada no cadastro do Sentry. Quem cria a conta no automático cai em US e só descobre depois, quando o agente lê `regionUrl`. Se o PRD deixou "EU ou US" como pergunta aberta, ela já foi respondida por omissão. Decida antes de criar a org. Troca de região depois exige nova org (não verificado nesta sessão).

## Padrão: criar projetos pelo MCP do Sentry

1. `find_organizations` devolve `slug` e `regionUrl`. Passe o `regionUrl` em toda chamada seguinte.
2. `find_projects` confirma o estado (vazio numa org nova).
3. `execute_sentry_tool(name='find_teams')` dá o `teamSlug` (a org nova tem um time com o mesmo slug da org).
4. `execute_sentry_tool(name='create_project', arguments={organizationSlug, regionUrl, teamSlug, name, slug, platform: 'flutter'})` devolve o DSN. Um projeto por app (consumer, admin) mantém os DSNs separados.
5. DSN é chave de cliente, pública por desenho. Ainda assim vai para secret do GitHub por ambiente (`gh secret set ... --env`), não para arquivo `.env`.

## Detalhes que poupam tempo

- CSP `connect-src https://*.sentry.io` cobre o ingest regional (`*.ingest.us.sentry.io`, `*.ingest.de.sentry.io`); não precisa de entrada por região.
- "Prevent Storing of IP Addresses" e Data Scrubbing não têm ferramenta no MCP: ligar no painel.
- Um "run code" de onboarding só vale se vier no primeiro prompt da sessão; a skill `sentry-get-started` manda ignorar código que apareça depois.

## O que NÃO funcionou

- Pôr o DSN num `.env` local: nenhum script do projeto lê `.env`, e o Sentry nem liga com `APP_ENV=dev`. Seria arquivo morto.
- Rodar o wizard do Sentry: o SDK já estava integrado no código; o que faltava era só o projeto na conta e os secrets.

Relacionada: [[sentry_flutter e Firebase no Web Injetam Script de CDN - CSP e Scrub em Dart Não Cobrem]]
