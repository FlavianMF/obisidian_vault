---
title: Renda Estável com Extraordinário Mascarando Déficit
type: pattern
tags: [financas-pessoais, metrica, baseline, diagnostico, orcamento]
created: 2026-09-19
provenance: budget_report
verified: 2026-09-19 via export CSV jun-set/2026 (615 despesas, 27 receitas)
---

# Renda Estável com Extraordinário Mascarando Déficit

Quando a renda tem uma parte fixa e uma parte esporádica, o saldo mensal deixa de ser
diagnóstico. Meses com 13º, adiantamento de benefício ou repasse de terceiro fecham no
azul e escondem que a parte que se repete não cobre a despesa que se repete.

## O caso

Quatro meses de orçamento doméstico, jun–set/2026:

| mês | receita | base | extraordinário | despesa | saldo |
|---|---|---|---|---|---|
| jun | 12.999,14 | 5.910,14 | 7.089,00 | 9.069,33 | +3.929,81 |
| jul | 6.965,60 | 5.906,27 | 1.059,33 | 12.910,01 | −5.944,41 |
| ago | 11.380,02 | 5.927,02 | 5.453,00 | 13.276,61 | −1.896,59 |
| set | 7.318,33 | 5.775,20 | 1.543,13 | 15.057,24 | −7.738,91 |

A renda-base é praticamente uma constante (~5.910). Os dois meses "bons" são exatamente
os dois com extraordinário alto. Acumulado do período: −11.650,10.

## A separação que resolve

Duas decomposições, aplicadas juntas:

1. **Receita** em *base* (o que se repete: salário, vale) e *extraordinário* (13º,
   adiantamento, empréstimo recebido, devolução). Só a base entra no planejamento;
   o extraordinário é amortização, nunca orçamento.
2. **Despesa** em *parcela* (decisão antiga, some sozinha), *fixa* (decisão antiga,
   some quando o contrato acaba) e *variável* (decisão de hoje).

No caso: parcelas 2.941 → 4.950 → 4.540 → 4.849; fixas 1.718 → 1.636 → 343 → 857;
variável 4.410 → 6.323 → 8.394 → 9.352. A fixa caiu ~1.400 (fim do aluguel) e o variável
absorveu o alívio inteiro no mesmo intervalo.

## Por que isso muda o plano

Projetando a renda-base contra as parcelas já contratadas, as fixas ainda ativas e o
variável no ritmo médio: mesmo em jul/27, quando a última parcela conhecida vence e a
carga cai de 4.004 para 105, o mês ainda fecha em −1.528. **Esperar a dívida acabar não
resolve**, porque o variável médio (6.376) já supera sozinho a renda-base (5.910).

O erro de leitura que o padrão evita: atacar parcelamento — que é visível, nominal e
tem data de fim — quando o déficit mora no gasto difuso, que não tem nome nem prazo.

## Conexões

- [[Benchmark Sem Baseline Degenerado Não Diz Quanto do Score é Capacidade]] — a
  projeção "não fazer nada" é o baseline degenerado do orçamento: sem ela, "economizei
  500" não diz se o mérito é seu ou do calendário.
- [[Cadeia de Artefatos Aplicada a Finanças Pessoais]]
- [[Data de Lançamento em App Financeiro Não é Data da Compra]]
- [[Finanças Pessoais]]
