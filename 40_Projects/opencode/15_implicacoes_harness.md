---
title: Implicações de design para um harness próprio
type: project
tags: [opencode, harness, architecture, design-synthesis]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

> Ver [[opencode]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Implicações de design para um harness próprio

[← Índice](00_indice.md)

Síntese das outras 14 seções, focada em: o que vale a pena copiar/adaptar do design do opencode ao construir um harness de orquestração de agentes (relevante ao trabalho de MCP/LLM tooling em torno do Capella — ver `notes/arquitetura_hibrida_mcp_capella.md`, `notes/metodologia_dev_mcp.md`).

## Padrões que valem reaproveitar

1. **API única, transporte plugável** (ver [04_client_server.md](04_client_server.md))
   Definir o contrato de servidor (tipos, rotas, schema) uma vez, e trocar só a implementação de transporte: RPC in-process para o caso local/single-user, HTTP+SSE real quando é preciso acesso remoto/multi-cliente. Evita duplicar lógica de cliente entre "modo embutido" e "modo servidor". Isso é diretamente aplicável se o harness próprio precisar rodar tanto embutido num processo CLI quanto exposto como serviço.

2. **Separação protocol/route no adapter multi-provider** (ver [05_providers_llm.md](05_providers_llm.md))
   `packages/llm` separa "como transformar o payload pra esse formato de API" (protocol) de "pra onde mandar e com que auth" (route). Permite adicionar um provider novo sem reescrever a lógica de streaming/normalização de evento. Padrão direto pra qualquer harness que precise suportar múltiplos providers de LLM (Anthropic, OpenAI, locais).

3. **Permission-as-deferred-promise** (ver [07_permissoes_seguranca.md](07_permissoes_seguranca.md))
   Em vez de bloquear o processo esperando input do usuário, a tool call cria uma promise pendente, publica um evento, e uma resposta assíncrona (via API ou hook de plugin) resolve a promise. Desacopla completamente o loop de execução do agente da UI de aprovação — a mesma tool call pode ser aprovada por um humano na TUI, por uma política em código (hook `permission.ask`), ou por um processo externo via API. É o design mais reaproveitável do projeto pra quem quer um approval gate que funcione tanto interativo quanto automatizado.

4. **Plugins com hooks em todo o ciclo de vida, não só "tools customizadas"** (ver [09_plugins.md](09_plugins.md))
   `tool.execute.before/after`, `permission.ask`, `chat.params/headers` cobrem os pontos de intercepção que um harness de automação realmente precisa: auditoria, redaction, rate limiting, política de aprovação, e reescrita de request de LLM — tudo sem precisar reimplementar o loop de agente. Comparar com abordagens que só expõem tool-calling customizado.

5. **Event-sourcing de sessão para auditoria/replay** (ver [03_agent_loop.md](03_agent_loop.md), Session V2)
   Separar "admissão do prompt" (evento durável, queryable) de "execução do prompt" (side-effecting) permite replay/auditoria sem re-executar contra o LLM, e permite process crash recovery sem perder o histórico. Compaction que troca só a *representação ativa* do modelo, preservando a transcrição completa, é um padrão sólido pra manter custo de contexto baixo sem perder rastreabilidade.

6. **Fail explicit em vez de degradar silenciosamente** (ver [05_providers_llm.md](05_providers_llm.md))
   Política deliberada do opencode: se uma combinação provider/rota não é suportada, falha com erro claro em vez de tentar "adivinhar" um comportamento degradado. Boa prática para um harness que vai rodar sem supervisão humana constante (CI, automação) — falha visível é melhor que comportamento silenciosamente errado.

## Riscos/pontos de atenção observados no próprio opencode

- **Coexistência de API v1/v2** ([12_headless_sdk_api.md](12_headless_sdk_api.md)): o projeto tem dois namespaces de rota (`/session/...` legado e `/api/session/...` novo) coexistindo — sinal de débito de migração em andamento. Recomendação prática: se for integrar com o opencode real via API, mirar o namespace `/api/*` + `@opencode-ai/sdk/v2`, que é a geração ativamente desenvolvida.
- **Branch default é `dev`, não `main`** — qualquer automação de clone/CI que assuma `main` como default vai quebrar silenciosamente.
- **Rotas `/experimental/*`** são explicitamente instáveis — não construir dependência de harness em cima delas sem monitorar changelog.
- **Dependência de fontes secundárias para história/governança** ([01_visao_geral_historia.md](01_visao_geral_historia.md)): a narrativa de rebrand SST→Anomaly e a disputa Charm/Crush vieram de blogs terceiros, não confirmadas contra uma fonte primária nesta pesquisa — não crítico pro harness técnico, mas relevante se for citar essa história em contexto formal (ex.: dissertação).

## Não é preciso adotar o opencode inteiro para reaproveitar esses padrões

Os pontos 1–6 acima são padrões arquiteturais que podem ser extraídos e aplicados a um harness escrito do zero (independente de stack — o opencode usa Effect-TS/Bun, mas os padrões (transporte plugável, protocol/route split, deferred-promise permission, hooks de plugin, event-sourcing) são portáveis pra qualquer stack, incluindo Python, que é provavelmente mais alinhado ao ecossistema py-capellambse/MCP já em uso no projeto Capella).

## Ver também

Todos os outros 14 arquivos desta pasta contêm o detalhe de implementação por trás de cada um desses padrões. Ver [00_indice.md](00_indice.md) para navegação por objetivo.
