---
title: Benchmark Sem Baseline Degenerado Não Diz Quanto do Score é Capacidade
type: trap
tags: [benchmark, metrics, evaluation, llm, methodology, research]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

# Benchmark Sem Baseline Degenerado Não Diz Quanto do Score é Capacidade

Um score de benchmark isolado é inauditável. Sem saber quanto um agente
**degenerado** — que não olha a entrada — tira na mesma suíte, não há como
separar capacidade do modelo de estrutura da prova.

## As duas evidências

**Baseline de entrada vazia.** No Vision QA do BenchCAD (arXiv:2605.10865), o
melhor modelo faz **0.587** e uma **imagem em branco tira 0.375**. Quase dois
terços do "desempenho" do topo são alcançáveis sem olhar nada — priors de formato
de pergunta, distribuição de resposta, chute estruturado. Sem essa linha
publicada, 0.587 parece muito melhor do que é.

**Métrica condicionada à execução sem a taxa de execução ao lado.** No mesmo
leaderboard, `openai/o3` tem o **maior IoU da tabela inteira (0.500)** e fica em
penúltimo no total (0.108), porque seu `exec_pct` é **5,6%**. A média de qualidade
foi calculada sobre a minoria que executou — os casos fáceis. Reportado sozinho,
aquele 0.500 seria estado da arte.

## Como evitar

1. Publicar **sempre** ao menos um baseline degenerado junto do resultado:
   entrada vazia, modelo trivial, resposta constante, ou sequência fixa que produz
   o esqueleto típico da tarefa.
2. Publicar **taxa de execução/completude** ao lado de toda métrica que só existe
   para os casos que completaram, e **declarar o denominador** de cada uma.
3. Desconfiar de qualquer benchmark de fornecedor que não traga nenhuma das duas
   coisas. Nos benchmarks internos do MecAgent não há n declarado, nem rubrica
   publicada, nem controle — e é material promocional publicado junto com o
   lançamento do modelo avaliado.

## Onde isso morde aqui

O framework de métricas de `projetos_ita/notes/framework_metricas_mbse_ia.md`
tem exemplo de relatório comparativo sem nenhuma linha de baseline e começa a
Dimensão B em "validade semântica", que já pressupõe que algo foi criado. As duas
correções (baseline degenerado + métrica B0 de taxa de execução) são baratas e
mudam a leitura de todo resultado já produzido.

## 🔗 Conexões
- [[Métricas de Avaliação de Geração de Artefato de Engenharia por LLM]]
- [[Reproduzibilidade e Open Science (2025)]]
- [[Escrita Acadêmica de Alto Impacto]]
