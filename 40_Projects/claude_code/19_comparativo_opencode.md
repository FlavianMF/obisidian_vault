---
title: Claude Code × opencode — dois desenhos de harness
type: project
tags: [claude-code, opencode, harness, comparison, design-synthesis]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Claude Code × opencode: dois desenhos de harness

[← Índice](00_indice.md)

Comparação com a pesquisa irmã em `notes/research/opencode/`. Os dois resolvem o mesmo
problema — agente de codificação no terminal, com ferramentas, permissão, MCP, plugins,
subagentes — e chegaram a arquiteturas bem diferentes.

> **Assimetria de fontes, declarada.** No opencode dá para ler o engine (MIT, source
> completo). No Claude Code lê-se o **contrato** e três mods; o engine é fechado. Então a
> comparação é justa sobre *modelo de extensão*, *forma da API* e *decisões de design
> documentadas*, e é desigual sobre *implementação interna do loop*.

## Quadro geral

| Eixo | **Claude Code** | **opencode** |
|---|---|---|
| Licença | Proprietária (Commercial ToS) | MIT |
| Stack | Binário único (perfil Bun), ~230 MB | TypeScript/Bun/Turborepo/Effect-TS/SolidJS |
| Arquitetura de processo | Cliente + daemon local; jobs em background; Remote Control | Cliente/servidor explícito, HTTP REST + SSE + WebSocket, mDNS |
| Superfície de automação | **Eventos** (84 nomes) + hooks clássicos (33) | **API HTTP** (~20 grupos de rota) + hooks de plugin (lista fixa) |
| Extensão em código | `register(on, options)`, hooks `($, e, next)` em cadeia de 5 tiers | `Plugin = (input) => Hooks`, objeto de hooks nomeados |
| Acesso ao mundo pelo plugin | **Só via `$`** — e todo acesso é evento | `client` SDK + `$` (Bun shell) + Node |
| Permissão | `tool.check` → `allow \| ask \| deny`, veredito sobe a cadeia | `Deferred` pendente + evento; resposta assíncrona resolve |
| Multi-provider LLM | Não exposto como abstração de plugin; providers via env/gateway | `packages/llm` com split protocol/route, adapter próprio + Vercel AI SDK |
| Persistência de sessão | JSONL em árvore (`parentUuid`), por projeto | SQLite/Drizzle, event-sourced (Session V2) |
| Teste de extensão | `claude plugin test` — o teste **é** o plugin do fundo | Testes do próprio projeto; sem kit de teste de plugin publicado |
| Política organizacional | Tiers + managed settings + MDM + mod `sec-default` | `experimental.policies` + config |

## A diferença que gera todas as outras

**opencode:** o plugin recebe um *cliente* e devolve um *objeto de hooks*. A superfície de
automação é a **API HTTP**; os hooks são uma lista fixa de pontos de intercepção
(`tool.execute.before/after`, `permission.ask`, `chat.params`, `chat.headers`, `event`,
`config`, `auth`, `provider`, `tool`).

**Claude Code:** o plugin recebe um *registrador* e engancha **eventos**. A superfície de
automação e a API são **a mesma coisa**: `$.fs.write(...)` é um dispatch que os hooks acima
veem ([02](02_modelo_engine_hooks.md)).

Consequências:

| | Claude Code | opencode |
|---|---|---|
| Interceptar uma capacidade nova | já dá: o evento existe porque a chamada existe | precisa de um hook novo no engine |
| Auditar tudo | `on("*")` | assinar `event` + rotas SSE, cobertura parcial |
| Sandboxar um plugin | hook acima dele nega eventos | não há mecanismo de tier |
| Mockar o mundo num teste | registrar hooks abaixo — é o kit oficial | framework de mock convencional |
| Custo de aprendizado | um modelo (`$`/`on`/`next`) para tudo | duas superfícies (API REST e hooks) |
| Acesso a partir de fora do processo | não é o caminho natural | é o caminho natural (HTTP) |

## Permissão: veredito em cadeia × promessa pendente

**opencode** (`permission/index.ts`): `Service.ask()` cria um `Deferred`, publica
`PermissionV1.Event.Asked`, e **bloqueia a tool até `reply()`** (`once | always | reject`).
Um harness externo dirigindo a API HTTP "encaixa" nesse ponto:
`GET /api/permission/request` + `POST /api/session/{id}/permission/{requestID}/reply`.

**Claude Code**: `tool.check` roda a cadeia inteira e produz `{ decision, reason?, rule? }`;
`ask` entrega ao *decisor do modo* (diálogo, classificador do modo automático, ou um host
headless). O ponto de encaixe externo é o **host**, não uma rota.

| | Claude Code | opencode |
|---|---|---|
| Quem decide | a cadeia de hooks; última palavra subindo vence | quem responde ao `Deferred` |
| Consultar sem executar | `$.tool.check(...)` roda a mesma cadeia e não executa | não há equivalente direto |
| Explicabilidade | `rule` traz a regra de settings como escrita (`Bash(git push:*)`) | a regra que casou, por `findLast` |
| Automatizar aprovação | hook em `tool.check` | hook `permission.ask` ou resposta pela API |
| Resistência a plugin hostil | tier: `user` não alcança o que `prepend` protege | sem camada de tier |
| Resolução de conflito | ordem de cadeia, determinística | última regra que casa vence |

O design do opencode é melhor para **aprovação por processo externo**; o do Claude Code é
melhor para **política que não pode ser burlada por quem instalou plugin**.

## Onde cada um é claramente mais forte

### opencode ganha

1. **Acesso externo é de primeira classe.** REST + SSE + WebSocket + SDK + mDNS. Para CI, um
   painel próprio ou um orquestrador multi-máquina, é o desenho certo.
2. **Multi-provider como arquitetura.** O split protocol (como transformar o payload) × route
   (para onde mandar, com que auth) permite adicionar provider sem mexer em streaming. No
   Claude Code isso é config e gateway, não abstração exposta.
3. **Source legível.** Para estudar *como* um loop de agente é feito, não há substituto.
4. **Event sourcing explícito de sessão** (Session V2), com replay sem re-executar contra o
   LLM.

### Claude Code ganha

1. **Um modelo só.** `$` / `on` / `next` cobre ferramenta, UI, prompt, config, fs, processo,
   rede, MCP, subagente. Menos conceitos, mais alcance.
2. **Autoridade por assento.** Os cinco tiers com `next.to` restrito a tiers gerenciados
   resolvem "política da organização versus plugin do usuário" estruturalmente
   ([11](11_mod_sec_default.md)). O opencode não tem resposta equivalente.
3. **Testabilidade.** O teste é o plugin do fundo da cadeia; `mock.clock` com
   `advance`/`settle` testa debounce e poll de verdade ([12](12_testing_kit.md)).
4. **Contrato que documenta comportamento, não só tipos.** Custo de cache de prompt, o que é
   pinado, o que acontece quando um hook falha, quem pode pular qual tier — tudo no docstring
   do evento que a pessoa vai hookar.
5. **Proveniência como dado, em toda parte.** `next.origin`, `e.provider`, `ConfigOrigin`
   (com `bridge` explicitamente "não atestavelmente a mão do dono"), `spawnedBy`,
   `origin.kind === 'person'`. O opencode tem bem menos disso.
6. **Ferramenta de produção como exemplo.** `mods/diff` são 779 arquivos de código real
   escritos contra a API, com testes — inclusive um teste de *custo*
   ([09](09_mod_diff.md)). O opencode documenta a API; o Claude Code mostra o uso.

## Onde os dois convergiram

Vale registrar porque convergência independente é sinal de que o padrão é correto:

- **allow / ask / deny** como vocabulário de permissão.
- **MCP** como protocolo de ferramenta externa, com o mesmo problema de OAuth, timeout e
  reconexão.
- **Subagente com config própria** (modelo, cwd, modo de permissão).
- **Compactação como evento interceptável**, com instruções reescrevíveis.
- **Config em camadas** com precedência declarada.
- **Transcrição preservada** — nenhum dos dois deixa plugin reescrever o registro do que
  aconteceu.

## Riscos, de cada lado

**Claude Code**
- API em *early access* atrás de feature flag, sem entrada no changelog: quebra silenciosa
  entre versões é um risco real ([01](01_visao_geral_superficie.md)).
- Licença proprietária: os padrões são estudáveis, o código **não é reutilizável**.
- Inventário de ferramentas built-in é gerado por versão — automação que assume um conjunto
  fixo quebra.
- Sem API HTTP de primeira classe: dirigir o harness de fora não é o caminho natural.

**opencode** (do que a pesquisa irmã registrou)
- API v1/v2 coexistindo (`/session/...` legado e `/api/session/...`) — dívida de migração.
- Branch default é `dev`, não `main`.
- Rotas `/experimental/*` instáveis.

## Ver também

- [20](20_implicacoes_harness_capella.md) — o que fazer com isso
- `notes/research/opencode/15_implicacoes_harness.md` — a síntese do lado de lá
