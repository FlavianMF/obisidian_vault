---
title: Providers e abstração multi-provider LLM
type: project
tags: [opencode, llm, multi-provider, api-design]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

> Ver [[opencode]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Providers e abstração multi-provider LLM

[← Índice](00_indice.md)

Duas camadas coexistem:

## a) `packages/llm` — abstração própria, schema-first

Package **standalone** (README/DESIGN.md/AGENTS.md próprios) que normaliza requests/responses/streaming entre providers, para que o código chamador nunca veja formatos específicos de provider.

Estrutura (`packages/llm/src/`): `llm.ts` (API unificada `request()`/`generate()`/`stream()`/`generateObject()`), `provider.ts`, `provider-error.ts`, `tool.ts`, `tool-runtime.ts`, `cache-policy.ts`, subpastas `protocols/`, `providers/`, `route/`, `schema/`, `utils/`.

**Adapters de provider confirmados** em `packages/llm/src/providers/`:
`anthropic.ts`, `openai.ts`, `openai-compatible.ts` (+ `openai-compatible-profile.ts`, `openai-options.ts` para backends de formato OpenAI genérico como DeepSeek/Cerebras/Groq/Fireworks/Together), `amazon-bedrock.ts`, `azure.ts`, `google.ts` (Gemini), `cloudflare.ts` (AI Gateway e Workers AI), `github-copilot.ts`, `openrouter.ts`, `xai.ts`.

**Design** (de `DESIGN.md`): tratamento de protocolo (transformação de request/response, ex. "anthropic/messages" vs "openai/responses") é mantido separado de roteamento (endpoint/auth/config), então todos os providers transmitem eventos pelo **mesmo formato normalizado**, independente do backend. `generateObject()` força deliberadamente extração estruturada baseada em tool-call em todo provider, em vez de confiar em modos JSON específicos de provider, para comportamento uniforme.

## b) `packages/core/src/aisdk.ts` — wrapper do Vercel AI SDK

Segunda camada de integração, separada, envolvendo o **Vercel AI SDK** (`@ai-sdk/*`, dependência fixada no `package.json` raiz: AI SDK 6.0.168, Anthropic SDK 3.0.111). Envolve `LanguageModelV3` do ecossistema de community-providers do AI SDK, com uma função `language()` que instancia e cacheia modelos backed-by-SDK de forma preguiçosa, uma classe `InitError`, e um wrapper customizado de fetch tratando timeouts de chunk SSE/sinais de abort.

Provavelmente usado para puxar a cauda longa de providers compatíveis com AI SDK sem o opencode ter que escrever um adapter manual para cada um, complementando os adapters hand-rolled de `packages/llm`.

## Config/roteamento

`packages/opencode/src/provider/` (`provider.ts`, `auth.ts`, `error.ts`, `model-status.ts`, `transform.ts`) + `packages/core/src/provider.ts`, `catalog.ts`, `models-dev.ts` (integração com o serviço de catálogo `models.dev`).

**Ordem de resolução de provider/modelo** (`specs/v2/provider-model.md`), pipeline de plugin fixo (13 plugins no total):

```
ModelsDev → Env → Account → Provider → Config → Discovery
```

Dá precedência determinística entre dados de catálogo remoto, variáveis de ambiente, contas vinculadas, defs estáticas de provider, config do usuário, e descoberta em runtime.

Modelos são aninhados sob providers porque "IDs de modelo só são únicos dentro de um provider". Habilitação não é booleana — registra *de onde* vem a disponibilidade (env/account/config customizada), para auditabilidade.

**Política de falha:** o doc afirma explicitamente que o session runner nativo suporta só um conjunto "estreito" de integrações maduras (ex. `openai/responses` via HTTP, `anthropic/messages`) e **falha explicitamente** em vez de degradar silenciosamente para rotas não suportadas — tradeoff deliberado de confiabilidade sobre cobertura.

## Regra de invariante do loop

Root `AGENTS.md` codifica uma regra a nível de agent-loop: *"Preserve one explicit `llm.stream(request)` call per provider turn"* — ou seja, não espalhar um turno lógico único em múltiplas chamadas de streaming ocultas.

## Ver também

- [14_autenticacao.md](14_autenticacao.md) para como credenciais de provider são armazenadas/injetadas
- [15_implicacoes_harness.md](15_implicacoes_harness.md) para a separação protocol/route como padrão reaproveitável
