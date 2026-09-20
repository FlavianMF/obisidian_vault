---
title: Finanças Pessoais
type: moc
tags: [moc, financas-pessoais, orcamento, diagnostico, project-methodology]
created: 2026-09-19
provenance: budget_report
---

# 💰 Finanças Pessoais (MOC)

Mapa do que o vault sabe sobre **ler um orçamento doméstico como sistema**: separar o que
é sinal do que é ruído no extrato, e transformar diagnóstico em plano verificável.

Nasceu do `budget_report` — quatro meses de export (jun–set/2026, 642 lançamentos)
analisados com o instrumental de engenharia de sistemas que já estava aqui.

## 🧭 Comece por aqui

- [[Renda Estável com Extraordinário Mascarando Déficit]] — a nota-mãe do diagnóstico:
  por que saldo mensal engana quando a renda tem parte esporádica, e a decomposição
  (base/extraordinário, parcela/fixa/variável) que desfaz o engano.
- [[Cadeia de Artefatos Aplicada a Finanças Pessoais]] — como virar plano: `E0..En`,
  aceite como teste negativo, V&V com o CSV do mês seguinte.

## ⚠️ Armadilhas de dado

- [[Data de Lançamento em App Financeiro Não é Data da Compra]] — as três datas do export,
  qual serve de eixo, e por que o calendário de gastos mostra cobrança e não consumo.

## 🛠️ Instrumental emprestado da engenharia de sistemas

- [[Benchmark Sem Baseline Degenerado Não Diz Quanto do Score é Capacidade]] — a projeção
  "não fazer nada" e a obrigação de declarar o denominador.
- [[Análise de Trade-off (Trade Study)]] — escolher onde cortar com peso e sensibilidade,
  em vez de intuição.
- [[Registro de Riscos - Birthday Counter]] — a forma da tabela de risco (prob. × impacto
  × mitigação), aqui com sintoma observável no extrato.
- [[Matriz de V&V - Birthday Counter]] — requisito → método → critério verificável.
- [[Plano de Fase em Etapas Mescláveis]] — `E0` fundação, `En` encerramento, aceite antes
  da execução.
- [[Playbook de Projeto - Erros Já Cometidos Como Artefato]] — o catálogo append-only de
  erro já pago.

## 📊 Artefato

- Relatório interativo jun–set/2026: https://claude.ai/artifact/JVFKiHcoKM5Lnsjsz1oyCc —
  diagnóstico, linha do tempo editável, marcação de divisão por pessoa, linha de base,
  trade study com pesos ajustáveis, plano `E0..E6` e matriz de V&V.
