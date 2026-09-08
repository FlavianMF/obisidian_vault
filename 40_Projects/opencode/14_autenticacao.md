---
title: Autenticação de providers
type: project
tags: [opencode, auth, credentials]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

> Ver [[opencode]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Autenticação de providers

[← Índice](00_indice.md)

Docs: [opencode.ai/docs/providers](https://opencode.ai/docs/providers/) · Fonte: `packages/opencode/src/auth/index.ts`, `packages/opencode/src/provider/*`

## Armazenamento de credenciais

`~/.local/share/opencode/auth.json` (modo `0o600`), escrito por `Auth.Service.set`. Três formatos de credencial (union de Effect Schema, `auth/index.ts`):

```ts
class Oauth { type: "oauth"; refresh; access; expires; accountId?; enterpriseUrl? }
class Api   { type: "api"; key; metadata?: Record<string,string> }
class WellKnown { type: "wellknown"; key; token }
```

O arquivo inteiro pode ser sobrescrito em memória via variável `OPENCODE_AUTH_CONTENT` (parseada como JSON) — **útil para injetar credenciais em CI sem escrever em disco**.

## CLI e TUI

- `opencode auth login` — setup interativo de credencial
- `opencode auth list`
- Na TUI, `/connect` percorre o fluxo de sign-in em opencode.ai/auth

## Catálogo de providers e customização

Catálogo dirigido por **Models.dev** (75+ providers via Vercel AI SDK). Customização a nível de config (`opencode.json` → `"provider"`): override de `baseURL` (para proxies), `blacklist`/`whitelist` de modelos, `options.apiKey` suportando substituição `{env:VAR}`/`{file:path}`. Providers customizados OpenAI-compatible podem ser declarados manualmente com `npm: "@ai-sdk/openai-compatible"`.

Modelos locais/self-hosted (Ollama, LM Studio, llama.cpp, etc.) são só providers OpenAI-compatible customizados apontando para endpoints `localhost`.

## Casos especiais

- **Amazon Bedrock** usa a cadeia de credenciais AWS/IAM roles em vez de `auth.json`.
- Auth do servidor da API HTTP (distinto de auth de provider) é HTTP Basic via `OPENCODE_SERVER_PASSWORD`/`OPENCODE_SERVER_USERNAME` (ver [12_headless_sdk_api.md](12_headless_sdk_api.md)).
- `experimental.policies` (`provider.use` allow/deny por ID) pode hard-bloquear um provider org-wide independente de credenciais existirem — ver [07_permissoes_seguranca.md](07_permissoes_seguranca.md).

## Ver também

- [05_providers_llm.md](05_providers_llm.md) — abstração multi-provider e ordem de resolução de config
- [12_headless_sdk_api.md](12_headless_sdk_api.md) — `--attach`/`--password`/`--username` para conectar a servidor remoto
