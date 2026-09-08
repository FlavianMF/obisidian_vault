---
title: Fontes
type: project
tags: [opencode, sources, references]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

> Ver [[opencode]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Fontes

[← Índice](00_indice.md)

## Repositório e API GitHub

- [github.com/anomalyco/opencode](https://github.com/anomalyco/opencode) — branch default: **`dev`** (não `main`)
- `api.github.com/repos/anomalyco/opencode` (+ `/languages`, `/topics`, `/contents/...`) — usado via `gh api` e WebFetch pra stats, linguagens, e conteúdo de arquivo cru
- Arquivos de fonte lidos diretamente (ref `dev`): `packages/opencode/src/tool/tool.ts`, `.../tool/task.ts`, `.../permission/index.ts`, `.../auth/index.ts`, `.../storage/storage.ts`, `.../cli/cmd/run.ts`, `.../cli/cmd/serve.ts`, `.../cli/cmd/mcp.ts`, `.../cli/cmd/tui.ts`, `.../session/{prompt,processor,tools}.ts`, `.../bus/global.ts`, `.../server/mdns.ts`, `packages/plugin/src/index.ts`, `packages/plugin/src/tool.ts`, `packages/core/src/global.ts`, `packages/core/src/database/database.ts`, `packages/core/src/aisdk.ts`, `packages/llm/src/{llm,provider,tool}.ts` + `providers/*.ts`, `packages/opencode/package.json`, `packages/sdk/js/package.json`, `packages/plugin/package.json`, `packages/sdk/openapi.json` (162 rotas REST enumeradas)
- Docs internas de design: `/CONTEXT.md`, `/AGENTS.md`, `/CONTRIBUTING.md`, `specs/project.md`, `specs/v2/session.md`, `specs/v2/provider-model.md`, `packages/llm/DESIGN.md`, `packages/codemode/codemode.md`

## Site de documentação oficial (opencode.ai)

- Índice: [opencode.ai/docs](https://opencode.ai/docs/)
- [/docs/cli](https://opencode.ai/docs/cli) · [/docs/config](https://opencode.ai/docs/config/) · [/docs/providers](https://opencode.ai/docs/providers) · [/docs/agents](https://opencode.ai/docs/agents) · [/docs/tools](https://opencode.ai/docs/tools/) · [/docs/custom-tools](https://opencode.ai/docs/custom-tools/) · [/docs/permissions](https://opencode.ai/docs/permissions/) · [/docs/policies](https://opencode.ai/docs/policies/) · [/docs/mcp-servers](https://opencode.ai/docs/mcp-servers/) · [/docs/plugins](https://opencode.ai/docs/plugins/) · [/docs/sdk](https://opencode.ai/docs/sdk/) · [/docs/server](https://opencode.ai/docs/server/) · [/docs/lsp](https://opencode.ai/docs/lsp) · [/docs/acp](https://opencode.ai/docs/acp/) · [/docs/share](https://opencode.ai/docs/share/) · [/docs/ecosystem](https://opencode.ai/docs/ecosystem)
- Não deep-fetched nesta rodada, mas listados na navegação — candidatos a follow-up: `/docs/enterprise`, `/docs/network`, `/docs/troubleshooting`, `/docs/windows`, `/docs/github`, `/docs/gitlab`, `/docs/go`

## Fontes secundárias (história/comparação — grau de confiança menor, marcado nos arquivos onde usado)

- [Pi vs OpenCode: After 100 Hours — Composio](https://composio.dev/content/pi-vs-opencode)
- [OpenCode — Learn AI Miraheze wiki](https://ai.miraheze.org/wiki/OpenCode)
- [OpenCode Developer Guide — Developers Digest](https://www.developersdigest.tech/blog/opencode-developer-guide-2026)
- [OpenCode Terminal AI Coding Agent — TechPillow](https://www.techpillow.co/blog/opencode-terminal-open-source-ai-coding-agent)
- [OpenCode background story — Tech Funding News](https://techfundingnews.com/opencode-the-background-story-on-the-most-popular-open-source-coding-agent-in-the-world/)
- [opencode (SST) — AI Wiki](https://aiwiki.ai/wiki/opencode)
- [OpenCode — Grokipedia](https://grokipedia.com/page/opencode)
- [OpenCode: The Terminal-Native AI Coding Agent — Medium](https://medium.com/@ananyavhegde2001/opencode-the-terminal-native-ai-coding-agent-that-actually-gets-it-5260c7ea8908)
- [OpenCode Quickstart — DEV Community](https://dev.to/rosgluk/opencode-quickstart-install-configure-and-use-the-terminal-ai-coding-agent-4kcb)
- [What Is OpenCode? — DataCamp](https://www.datacamp.com/blog/what-is-opencode)

## Metodologia da pesquisa

Coleta feita por 3 subagentes de exploração rodando em paralelo (WebFetch + WebSearch + GitHub API, read-only), cada um com foco distinto: (1) visão geral/história/features, (2) arquitetura interna/monorepo/agent loop, (3) tools/MCP/permissões/config/headless/SDK/API. WebFetch sumariza conteúdo via modelo intermediário em vez de retornar bytes crus — trechos de código citados nos arquivos 01-15 são "como reportado" pelas ferramentas, não `cat` byte-exato, mas estrutura e nomes de arquivo foram corroborados entre múltiplas leituras independentes onde possível.
