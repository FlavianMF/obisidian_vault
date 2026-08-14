---
title: Model Context Protocol (MCP)
type: concept
tags: [mcp, llm, protocol, tool-use]
created: 2026-08-14
provenance: capella_mcp
project: capella_mcp
---

# Model Context Protocol (MCP)

Protocolo aberto, baseado em **JSON-RPC 2.0**, que padroniza como
aplicações LLM (**hosts**) se conectam a fontes de contexto e ferramentas
externas (**servers**) através de um **client** embutido no host — em vez
de N integrações ad hoc por app, uma interface comum. Inspirado no
[Language Server Protocol
(LSP)](https://microsoft.github.io/language-server-protocol/): o LSP
padronizou "editor ↔ servidor de linguagem", MCP padroniza "app de LLM ↔
fonte de contexto/ferramentas".

Anunciado pela Anthropic em 25/11/2024, criado por David Soria Parra e
Justin Spahr-Summers ([[Soria Parra & Spahr-Summers 2024]]). Hoje é projeto
aberto hospedado pela Linux Foundation (org `modelcontextprotocol` no
GitHub), mantido por David Soria Parra e Den Delimarsky — ver
[[Model Context Protocol 2025]] pra spec normativa completa.

## Handshake

```
Client → Server : initialize (versão do protocolo, capabilities do client)
Server → Client : initialize response (capabilities do server, campo "instructions")
Client → Server : notifications/initialized
```

As duas pontas só podem usar, dali em diante, as capabilities negociadas
nesse handshake — é isto que decide, por exemplo, se `sampling` pode ser
usado naquela sessão.

## As seis primitivas

| Primitiva | Lado | Quem controla | Papel |
|---|---|---|---|
| `resources` | server | aplicação | dados/contexto expostos ao client |
| `tools` | server | **modelo** | funções que o modelo escolhe chamar sozinho |
| `prompts` | server | **usuário** | templates de mensagem acionados explicitamente |
| `sampling` | client | server pede, usuário aprova | server pede pro client rodar uma completion LLM |
| `roots` | client | — | limites de filesystem/URI em que o server pode operar |
| `elicitation` | client | server pede, usuário responde | server pede info adicional ao usuário |

A distinção **model-controlled (tools) vs. user-controlled (prompts) vs.
application-controlled (resources)** é o eixo central pra entender "quem
decide" usar cada primitiva — não é só uma questão de nomenclatura.

## Relação com system prompts

O ponto de contato direto entre MCP e "system prompt" é o campo
**`instructions`**, devolvido pelo server na resposta do `initialize`:
texto livre que o client é esperado incorporar como guia de uso daquele
server — na prática, um trecho de contexto que molda como o modelo entende
e usa o server, funcionalmente equivalente a uma seção de system prompt.

Uma segunda via, mais granular, é a `description` (e `annotations`) de
cada tool: também vira contexto que o modelo lê antes de decidir uma ação,
só que por tool em vez de uma vez só no handshake. A spec trata isso como
**untrusted** por padrão (annotations podem ser forjadas por um server mal
intencionado — vetor de "tool description injection").

## Como o protocolo permite "direcionar" (steering) o modelo

Do mais amplo ao mais pontual:

1. **`instructions` no handshake** — contexto de sessão inteira.
2. **`tools[].description` / `annotations`** (`readOnlyHint`,
   `destructiveHint`, `idempotentHint`, `openWorldHint`) — prompt
   engineering implícito por tool.
3. **`isError: true`** no resultado de uma tool call — feedback acionável
   pro modelo se autocorrigir, distinto de erro de protocolo JSON-RPC puro.
4. **`prompts` primitive** — templates prontos que o *usuário* aciona,
   padroniza um fluxo sem depender do modelo "lembrar" dos passos.
5. **`sampling`** — server pede uma chamada LLM adicional ao client
   (sub-agentes), com o usuário controlando se acontece, o prompt exato
   enviado, e o que o server vê do resultado — desenho deliberado pra
   impedir o server de extrair prompts arbitrários do usuário.

## Aplicação prática — `capella-mcp`

Ver `docs/mcp-protocol.md` no repo `capella_mcp` (nota irmã desta, com o
mesmo conteúdo ancorado no projeto). `capella-mcp` usa transporte **stdio**
(container Docker, decisão `0003-empacotamento-docker`) e só as primitivas
`resources` + `tools` — não usa `prompts`, `sampling`, `roots` nem
`elicitation`. O `MCPServer` é instanciado só com o nome, sem passar
`instructions=` (parâmetro que o SDK Python já expõe) — gap concreto: dá
pra descrever ali o fluxo esperado
`list_layers → list_elements → get_element → create_element/update_element`
sem depender do system prompt do host. A convenção `isError: true` já é
seguida (decisão `0004-escopo-v1-leitura-e-escrita`), conectando a prática
do projeto de volta à spec.

Ver também [[Empacotar App GUI Headless + Servidor MCP numa Única Imagem Docker]]
pro padrão de empacotamento que viabiliza rodar o server MCP + Capella
headless no mesmo container.
