---
title: Implicações para o harness próprio (Capella/MBSE)
type: project
tags: [claude-code, harness, capella, mbse, design-synthesis]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Implicações para o harness próprio (Capella / MBSE)

[← Índice](00_indice.md)

Síntese dos 19 capítulos anteriores, dirigida ao trabalho em curso:
`capella_mcp` (servidor MCP de acesso ao modelo Capella), `capella_llm_window`
(plugin Eclipse RCP com a janela de chat), e a arquitetura híbrida descrita em
`notes/arquitetura_hibrida_mcp_capella.md` (py-capellambse para leitura rápida, MCP Docker
para escrita e diagramas Sirius).

Nada aqui propõe adotar Claude Code nem copiar código dele — a licença é proprietária
([01](01_visao_geral_superficie.md)). O que se extrai são **padrões arquiteturais**, e cada um
é avaliado contra o que este projeto realmente precisa.

## Os cinco padrões que valem mais neste contexto

### 1. Toda capacidade é um evento interceptável

O padrão de [02](02_modelo_engine_hooks.md): não existe "API que o plugin chama" separada de
"eventos que o plugin escuta". A chamada **é** o evento.

Aplicação direta ao `HybridBridge`: em vez de `HybridBridge` decidir internamente entre
py-capellambse e MCP Docker, definir uma superfície de operações
(`model.listElements`, `model.getElement`, `model.createElement`, `diagram.create`,
`diagram.export`, …) onde cada operação atravessa uma cadeia antes de chegar ao executor.

Isso resolve, com um mecanismo só, coisas que hoje seriam código ad hoc espalhado:
- **roteamento** rápido/pesado (um hook decide se a operação vai para py-capellambse ou sobe
  o Docker);
- **cache** de leitura (um hook acima responde `{ value }` sem descer);
- **auditoria** de tudo que a LLM tentou fazer no modelo, para a dissertação;
- **medição de latência** por operação, sem instrumentar cada implementação;
- **dry-run** (um hook nega escrita e devolve o que teria acontecido).

Na arquitetura atual, cada um desses seria um `if` a mais no bridge.

### 2. Fachada nomeada em vez de passar o mundo

O padrão do `mods/diff` ([09](09_mod_diff.md)): no `session.start` o mod constrói um objeto
`Host` com 19 membros, cada um escrito `$.noun.event(...)`, e **todo o resto do código toma
`Host`, não `$`**.

Aplicação: definir um `CapellaHost` (ou manter o nome `HybridBridge`, mas como *tipo*) que
enumere exatamente o que o lado LLM pode fazer com o modelo. Ganhos:
- a superfície de capacidade da IA sobre o modelo Capella vira um artefato legível — algo
  citável na dissertação, não implícito no código;
- trocar py-capellambse por outra lib, ou o MCP Docker por um Capella embarcado, não toca em
  nada acima da fachada;
- testar o orquestrador sem Capella nenhum passa a ser natural.

### 3. Proveniência como dado, não como contexto implícito

O Claude Code carrega origem em toda parte: `next.origin` ({plugin, tier}, escrito só pelo
host), `e.provider` pinado, `ConfigOrigin` com `bridge` marcado como "não atestavelmente a
mão do dono" ([15](15_config_settings.md)), `origin.kind === 'person'`, `spawnedBy`.

Aplicação ao MBSE, onde isso vale ainda mais que num harness genérico: **todo elemento criado
ou modificado no modelo deveria carregar quem pediu** — a pessoa, a LLM por iniciativa
própria, ou um agente de teste. Um modelo Capella que a IA tocou sem esse registro é
difícil de auditar depois, e a auditabilidade é exatamente o que uma dissertação sobre
IA em MBSE precisa demonstrar.

Isto se conecta com a metodologia de dois agentes já descrita em
`notes/metodologia_dev_mcp.md` (agente desenvolvedor + agente usuário): com proveniência
gravada, as "anotações de limitação" do agente usuário deixam de ser prosa e viram dado.

### 4. Decisão de permissão explicável e persistida

De [05](05_sistema_tools.md) e [16](16_runtime_local_observado.md): o veredito é
`{ decision, reason, rule }` — traz a **regra que decidiu, como escrita** — e
`permissionMode`/`toolDenialKind` são **gravados na transcrição**, não só aplicados.

Aplicação: operações de escrita no modelo Capella são destrutivas e caras de reverter. Um
gate `allow | ask | deny` com regra nomeada (`createElement(LogicalComponent:*)`,
`deleteDiagram(*)`) e decisão persistida dá:
- reversibilidade informada;
- material empírico para o framework de métricas (`notes/framework_metricas_mbse_ia.md`):
  quantas operações foram negadas, por qual regra, em que fase Arcadia.

E o análogo de `$.tool.check` — consultar "isso seria permitido?" sem executar — é útil no
próprio prompt: a LLM pode saber o que não adianta tentar.

### 5. Transcrição como JSONL em árvore, volume fora dela

De [16](16_runtime_local_observado.md): uma linha por evento, `parentUuid` formando árvore,
`version` em cada linha, subagente com transcrição própria, resultado volumoso em
`tool-results/<id>.txt` referenciado por id.

Aplicação: um `export_to_json` de subset do modelo, ou um PNG de diagrama exportado, **não
deve entrar na transcrição**. Referência por id, arquivo ao lado. E `version` por linha é o
que vai permitir ler as sessões de hoje daqui a um ano, depois de o formato mudar — relevante
para um trabalho que vai durar mais que o código.

## Os padrões que **não** valem aqui (e por quê)

Registrar o que descartar é tão útil quanto o que adotar.

| Padrão | Por que não |
|---|---|
| **Cinco tiers de autoridade** | Resolvem "organização × plugin instalado pelo usuário". Este projeto não tem administrador de frota nem plugins de terceiros. Dois níveis (política do projeto / sessão) bastam. |
| **Ambiente isolado por plugin** (sem fs/rede/processo) | Custo alto de implementação, e aqui não há código de terceiro rodando. |
| **UI como evento** (`ui.render`, tabela de elementos por superfície) | A UI é SWT/JFace dentro do Eclipse; o padrão não transporta. |
| **Binário único auto-atualizável** | Distribuição é plugin Eclipse + Docker. Problema diferente. |
| **Marketplace / mods built-in** | Não há ecossistema de extensão a servir. |

## Onde este estudo diverge do que o opencode sugeriu

A pesquisa do opencode (`notes/research/opencode/15_implicacoes_harness.md`) recomendou
**API única com transporte plugável** (RPC in-process e HTTP+SSE) e **permission como
deferred promise**. Este estudo não contradiz, mas reordena a prioridade:

- A **cadeia de eventos** deveria vir **antes** da API HTTP. Ela é o modelo interno; a API é
  uma forma de expô-lo. Fazer o contrário (API primeiro) leva a duas superfícies para manter,
  que é justamente a dívida visível no opencode (`/session/...` × `/api/session/...`,
  [19](19_comparativo_opencode.md)).
- **Deferred promise** e **veredito em cadeia** são complementares, não alternativos: a cadeia
  produz `ask`, e o `ask` é resolvido por uma promessa pendente que a UI do plugin Eclipse
  (ou uma política em código) responde. É exatamente o que o Claude Code faz ao entregar o
  `ask` ao "decisor do modo".

## Ordem sugerida de adoção

Do mais barato com maior retorno para o mais caro:

1. **Proveniência** em toda operação de escrita no modelo. Um campo. Retorno imediato para
   auditoria e métricas.
2. **Fachada tipada** (`CapellaHost`) entre o orquestrador e as duas implementações
   (py-capellambse / MCP Docker). Refatoração contida, e destrava o teste sem Capella.
3. **Transcrição JSONL** com árvore e volume externo, substituindo qualquer log ad hoc.
4. **Gate `allow|ask|deny`** com regra nomeada e decisão persistida, sobre a fachada.
5. **Cadeia de hooks** sobre a fachada — só quando houver mais de um interessado por operação
   (cache + auditoria + roteamento). Antes disso, é complexidade sem cliente.
6. **API HTTP** por último, se e quando houver consumidor externo real.

## Uma nota metodológica

Os dois casos estudados chegaram, por caminhos independentes, ao mesmo vocabulário de
permissão (`allow`/`ask`/`deny`), ao mesmo tratamento de compactação como ponto
interceptável, e à mesma regra de **não deixar plugin reescrever o registro do que
aconteceu**. Convergência independente entre dois projetos sem relação é o sinal mais
confiável de que um padrão é estrutural e não moda — e é um argumento citável, não só uma
escolha de implementação.

## Ver também

- [19](19_comparativo_opencode.md) — a comparação que fundamenta este capítulo
- `notes/arquitetura_hibrida_mcp_capella.md` — a arquitetura sobre a qual isto incide
- `notes/framework_metricas_mbse_ia.md` — onde a proveniência e o gate viram métrica
