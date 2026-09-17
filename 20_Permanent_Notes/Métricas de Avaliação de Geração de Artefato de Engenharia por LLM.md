---
title: Métricas de Avaliação de Geração de Artefato de Engenharia por LLM
type: concept
tags: [metrics, benchmark, llm, cad, mbse, evaluation, code-generation]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

# Métricas de Avaliação de Geração de Artefato de Engenharia por LLM

Destilado do estudo do **BenchCAD** (arXiv:2605.10865 — acadêmico, código MIT,
dataset CC BY 4.0) e do ecossistema text-to-CAD de 2026 (CADBench, CADTests,
Text2CAD-Bench). Vale para qualquer domínio onde o LLM gera um **artefato de
engenharia editável** — CAD, modelo MBSE, esquema, infraestrutura como código —
e não texto. Pesquisa completa em `projetos_ita/notes/research/mecagent/`.

## O conjunto mínimo

| Métrica | Mede | Ponto cego |
|---|---|---|
| `exec_pct` | % de artefatos gerados que executam sem erro | não diz nada sobre estar certo |
| Similaridade com o alvo (IoU, F1 estrutural) | quanto do resultado bate com o esperado | superestima acerto grosseiro |
| **Recall de operações essenciais** | fração das operações/elementos críticos gerados corretamente | é a única que olha o *como*, não o *quê* |
| Acurácia normalizada pelo gap | quanto do caminho até o alvo a edição percorreu | herda os limites da métrica de similaridade |
| Teste de comportamento sob mutação | se o artefato é de fato paramétrico/estrutural | caro de construir |

## As três lições que mais mudam resultado

**1. Similaridade alta convive com construção errada.** No leaderboard do
BenchCAD, o CADEvolve v3 tem IoU **0.75** (empatado com o topo) e recall de
operação essencial **0.371**: produz o sólido quase certo substituindo sweep/loft
por sketch-and-extrude. Para uma imagem, dá na mesma. Para um artefato que
alguém vai editar amanhã, é outro objeto. Por isso existe métrica sobre o
*programa*, não só sobre o resultado. Em MBSE o análogo é ter os elementos certos
pendurados no pai errado — ver [[Paisagem de MCP Servers para MBSE e CAD]].

**2. Métrica condicionada à execução mente sozinha.** Ver
[[Benchmark Sem Baseline Degenerado Não Diz Quanto do Score é Capacidade]].

**3. Testar comportamento vale mais que comparar forma.** O CADTests
(arXiv:2605.07807) não compara geometria: **varia os parâmetros do modelo gerado e
verifica se ele se atualiza como deveria**. Um modelo com IoU 0.95 e tudo
hard-coded quebra ao mudar um diâmetro — pela métrica geométrica, é quase
perfeito. Generalizando: *aplique uma mutação ao artefato gerado e veja se a
estrutura sobrevive*. É o que separa um modelo de um desenho de modelo.

## Duas consequências de projeto

- **A métrica vira função de reward.** O CAD-Coder (arXiv:2505.19713) usa Chamfer
  Distance como reward de RL com GRPO. Quem define bem a métrica ganha o pipeline
  de treino junto. Argumento para definir métrica com rigor *antes* de precisar.
- **Modelo pequeno especializado bate frontier em tarefa estreita e verificável
  por execução.** Um qwen3-2b com RL marca 0.768 no BenchCAD contra 0.397 do
  melhor generalista.

## 🔗 Conexões
- [[Benchmark Sem Baseline Degenerado Não Diz Quanto do Score é Capacidade]]
- [[Gerar Código da API Nativa em Vez de Manipular o Modelo Direto]]
- [[Paisagem de MCP Servers para MBSE e CAD]]
- [[MBSE com Agentic AI]]
