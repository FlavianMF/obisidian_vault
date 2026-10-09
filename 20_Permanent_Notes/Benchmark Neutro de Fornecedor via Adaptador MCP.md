---
title: Benchmark Neutro de Fornecedor via Adaptador MCP
type: pattern
tags: [benchmark, mcp, agentic-ai, evaluation, pass-k, mbse]
created: 2026-10-09
provenance: projetos_ita
seen_in: [projetos_ita]
verified: 2026-10-09 via levantamento de produtos (Obeo, IBM, SodiusWillert, Cameo bridges, Fabric Generator, OpenKer usam MCP)
confidence: medium
---

# Benchmark Neutro de Fornecedor via Adaptador MCP

## Padrão

Em 2026 o MCP virou a porta de entrada padrão das ferramentas de engenharia para agentes: Obeo AI for Capella, IBM Engineering AI Hub, SodiusWillert (Rhapsody), pontes do Cameo, Capella Fabric Generator, OpenKer. Por isso um benchmark de agentes **não precisa ficar preso a um produto**. Basta:

1. Um **adaptador fino por sistema sob teste (SUT)**, que mapeia as ações e observações do benchmark para as tools daquele produto.
2. Um **runner de agente** com modelo, seed, temperatura e versão registrados num manifesto.
3. Uma **exportação do modelo final** para oráculos independentes do produto, em camadas: validade, diff estrutural, regras de metodologia e rubrica humana com concordância entre avaliadores.
4. Um **split público de desenvolvimento** e um **split oculto de teste**, para o fornecedor não ajustar o produto para o teste.

Métricas: pass@1, pass@k, **pass^k** (todas as k execuções corretas, que é a métrica de segurança), taxa de escape do gate, taxa de escrita silenciosamente errada e taxa de ações destrutivas.

## Por que funciona

- Neutralidade dá citação e autoridade: qualquer fornecedor ou pesquisador pode rodar.
- O MCP reduz o custo de integrar um produto novo a um adaptador.
- Em MBSE, nenhum paper encontrado (out/2026) reporta pass^k, e não existe benchmark Capella/Arcadia.

## Armadilhas

- **Termos de uso:** alguns fornecedores proíbem publicar benchmark do produto sem autorização. Pergunte antes de comparar produtos comerciais.
- **Licença dos fixtures:** verifique a licença dos modelos de exemplo, como o IFE do Capella, antes de redistribuir.
- **Validade do oráculo:** diff estrutural superestima a correção. É preciso medir o oráculo contra especialistas.
- **Baseline:** inclua um baseline degenerado. Ver [[Benchmark Sem Baseline Degenerado Não Diz Quanto do Score é Capacidade]].

## Instância

MERIT (Model Edit Reliability In Tools): especificação em `projetos_ita/notes/tese/02_benchmark_aberto_spec.md`, que reaproveita o harness `/eval` do `capella_llm_window`. Ver [[Direcao_Tese_e_Carreira]].
