---
title: Paisagem de MCP Servers para MBSE e CAD
type: concept
tags: [mcp, mbse, sysml, capella, cad, competitive-landscape]
created: 2026-08-15
provenance: capella_mcp
project: capella_mcp
---

# Paisagem de MCP Servers para MBSE e CAD

Pesquisa comparativa (Aug/2026) posicionando o `capella-mcp` contra tudo
que foi encontrado publicamente disponível — outros MCP servers pra
ferramentas MBSE, MCP servers pra CAD/engenharia em geral, e o próprio
spec do MCP. Relatório visual completo publicado como Artifact
(`docs/second_brain` não versiona o HTML, só esta nota condensada) — ver
também [[Model Context Protocol (MCP)]] pra fundamentos do protocolo.

## Achado principal: nicho aberto

**Não existe nenhum MCP server pra Eclipse Capella hoje.** Toda ocorrência
de "Capella" nos registries públicos (glama.ai, mcp.so, mcpservers.org)
é o produto de banco de dados em nuvem da Couchbase, mesmo nome, projeto
não relacionado. `capella-mcp` não tem concorrente direto — o
enquadramento certo não é "estamos perdendo pra X", é "o que ferramentas
MBSE/CAD adjacentes já resolveram que a gente ainda não".

## Comparáveis MBSE encontrados

| Projeto | Alvo | Tools | ★ | Nota |
|---|---|---|---|---|
| **cameo-mcp-bridge** | Cameo/MagicDraw (SysML, UML) | 162 | 32 | mais rico encontrado; sem auth, tool de macro Groovy = execução arbitrária de JVM, autor mesmo avisa que não é seguro pra produção compartilhada |
| SysML v2 API MCP Server | OMG SysML v2 API & Services | — | 22 | rótulo do próprio autor: "work in progress, by no means suitable for productive use" |
| Enterprise Architect MCP (oficial, Sparx) | Sparx EA | — | — | vendor-native; write/delete atrás de flags de lançamento explícitas `-enableEdit`/`-enableDelete` — padrão de permissão em camadas digno de nota |
| ea_mcp (comunidade) | Sparx EA | — | 4 | early-stage, um contribuidor, só criação de diagrama UML |
| IBM Engineering Rhapsody MCP (10.0.3) | IBM Rhapsody | — | — | vendor-native, read-only, public preview |

**PTC Windchill Modeler**: sem MCP server publicado; comunidade PTC
("currently evaluating roadmap plans for MCP integration").

## Padrões emprestáveis do mundo CAD (fora de MBSE)

- **BlenderMCP** (~17.800 estrelas — o MCP server de ferramenta
  criativa/engenharia mais adotado encontrado em toda a pesquisa) expõe
  aviso de segurança franco: executa código Python gerado por LLM dentro
  do Blender sem sandbox, recomenda VM isolada.
- Cohort de **AutoCAD/FreeCAD MCP servers** converge em: (a) **backend
  duplo** — automação COM ao vivo *e* caminho headless via formato de
  arquivo (ex. DXF via `ezdxf`), funciona com ou sem o app licenciado
  rodando; (b) **validação de domínio como tool de primeira classe** (ex.
  checagem de GD&T/tolerância), em vez de deixar só pro LLM raciocinar;
  (c) granularidade bem mais fina de tools — 100+ tools estreitas, contra
  as 8 (mais amplas) do `capella-mcp`.

## Cobertura do spec MCP 2025-11-25

`capella-mcp` usa 2 das 7 primitivas: `tools` + `resources` (sem
`outputSchema`/`structuredContent`, sem paginação por cursor, sem
subscriptions/`listChanged`). **Nenhum** dos comparáveis MBSE/CAD
pesquisados usa `prompts`, `sampling`, `elicitation`, `roots` ou
`progress` — não é uma lacuna exclusiva deste projeto, é espaço em
branco em toda a categoria.

## Literatura acadêmica — 4 clusters de capacidade validados, zero como MCP server

- **Requisitos → geração de modelo**: Timperley et al. 2025 (*J.
  Engineering Design* 36(4)) acoplou um LLM ao Capella pra gerar
  arquitetura de espaçonave em 3 tarefas reais de design; saída julgada
  de boa qualidade, às vezes mais detalhada que baseline humano.
- **Verificação de cumprimento de requisito contra o grafo do modelo**:
  arXiv:2503.14130 usou dois modelos Capella de missão espacial como
  conjunto de teste; intervenção direcionada em attention heads atingiu
  "precisão perfeita" no holdout.
- **Consulta em linguagem natural sobre conteúdo do modelo**: *Systems*
  (MDPI) 14(1):83, 2026 — interface de retrieval pra artefatos de
  arquitetura de sistema, feita pra consumo humano e de IA.
- **Checagem de consistência semântica / fault localization**:
  arXiv:2606.23395 — framework de LLM com grafo de conhecimento pra
  localizar falhas em modelos SysML v2.

Revisão sistemática de 2025 (*J. Systems & Software* 226) achou que
extração de requisitos especificamente em Arcadia/Capella "precisa de
mais evidência" comparado a SysML — exatamente a lacuna que a proposta de
mestrado por trás deste projeto (ver
`docs/second_brain/40_Projects/Mestrado_ITA/Proposta_Pesquisa_MBSE_AI.md`)
está posicionada pra preencher.

## Roadmap de melhorias (esforço crescente)

1. **Quick wins técnicos**: `export_diagram` glob não-recursivo;
   `create_element` faltando `PhysicalComponent`/`PhysicalFunction`/
   `ConfigurationItem`; testes de integração faltando pra
   create_diagram/delete_diagram/export_diagram; docs desatualizados;
   paginação em `list_elements`.
2. **Alinhamento ao spec**: `progress` em chamadas headless longas;
   `elicitation` pra desambiguação/confirmação destrutiva; `prompts`
   reutilizáveis; permissão em camadas tipo EA MCP
   (`-enableEdit`/`-enableDelete`).
3. **Alinhado à pesquisa** (maior retorno pro objetivo do projeto):
   rastreabilidade/cumprimento de requisito, consulta NL sobre o modelo,
   checagem de consistência semântica, diagramas além de "breakdown".

## 🔗 Conexões
- [[Model Context Protocol (MCP)]]
- [[Capella Breakdown Diagram - root_id Infere Tipo Concreto, Não o Declarado]]
- [[Capella MBSE]]
