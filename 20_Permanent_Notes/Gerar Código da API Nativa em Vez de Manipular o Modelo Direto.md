---
title: Gerar Código da API Nativa em Vez de Manipular o Modelo Direto
type: pattern
tags: [llm, code-generation, cad, mbse, capella, architecture, agentic-ai]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

# Gerar Código da API Nativa em Vez de Manipular o Modelo Direto

Quando um LLM precisa produzir um artefato de engenharia (modelo CAD, modelo
MBSE, diagrama), a saída dele **não deve ser o artefato**. Deve ser o **programa
na API nativa da ferramenta** que constrói o artefato — e quem executa é a
ferramenta.

## Quem faz isso

| Sistema | Linguagem gerada | Executor |
|---|---|---|
| MecAgent (copiloto de CAD, seed US$3M em 2026) | macro VBA/C# (`.swp`/`.swb`) | SOLIDWORKS, Inventor |
| BenchCAD, CAD-Coder, Text-to-CadQuery | CadQuery (Python) | kernel OCC, headless |
| `capella_mcp` | Python4Capella | Capella via EASE |

A formulação do MecAgent: *"The resulting geometry is not approximated: it is
built by the software itself."*

## Por que

1. **O solver não é seu problema.** Restrição geométrica, cota, containment,
   tipagem do metamodelo — resolvidos por software maduro. O LLM não precisa
   *saber* o domínio formal, precisa saber chamar a API.
2. **A saída nasce editável.** Mesh gerado é beco sem saída: sem árvore de
   features, sem parâmetro. Resultado de macro é modelo paramétrico normal,
   indistinguível de um feito à mão.
3. **A convenção da ferramenta sai de graça.** Nomenclatura, unidades, estrutura,
   anotação.

## O custo, que é a parte esquecida

**O erro migra de semântico para sintático/de execução.** O programa pode não
compilar, lançar exceção, ou rodar e produzir artefato degenerado. Três
consequências obrigatórias:

- **Taxa de execução vira métrica de primeira classe** — ver
  [[Benchmark Sem Baseline Degenerado Não Diz Quanto do Score é Capacidade]].
- **O erro de execução tem que realimentar o modelo.** O MecAgent faz parsing da
  saída de console do CAD num loop "edit → execute → verify"; o Text-to-CadQuery
  (arXiv:2505.06507) devolve a mensagem de erro ao modelo para auto-correção.
  Sem esse loop, o padrão entrega menos do que promete.
- **Executar código gerado no documento aberto do usuário exige sandbox ou
  rollback.** Nenhuma fonte pública do MecAgent menciona qualquer um dos dois —
  é a lacuna de segurança mais evidente do produto deles.

## 🔗 Conexões
- [[Métricas de Avaliação de Geração de Artefato de Engenharia por LLM]]
- [[Paisagem de MCP Servers para MBSE e CAD]]
- [[Python4Capella get_contents() é Snapshot Desconectado - Containment Real Exige get_owned_X()]]
