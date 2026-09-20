---
title: Data de Lançamento em App Financeiro Não é Data da Compra
type: trap
tags: [financas-pessoais, dados, csv, serie-temporal, analise, armadilha]
created: 2026-09-19
provenance: budget_report
verified: 2026-09-19 via export CSV jun-set/2026
---

# Data de Lançamento em App Financeiro Não é Data da Compra

Export de app de controle financeiro traz três datas por linha — `Lançamento`,
`Vencimento`, `Efetivação` — e o nome mais intuitivo é justamente o que não serve de eixo
do tempo.

## Armadilha

Duas distorções independentes, que se somam:

**1. `Lançamento` é o instante da digitação.** Num export de 615 despesas, 129 linhas
carregam o mesmo timestamp: `02/06/2026 13:26`. É a importação inicial, não compras
daquele minuto. Agrupar despesa por mês de lançamento produzia 27.483 em junho contra
9.069 pelo vencimento — um erro de 3×, no mês de abertura, exatamente onde o analista
ainda não desconfia de nada.

**2. Cartão desloca a compra para a data da fatura.** Pelo vencimento, o gasto concentra
em três dias: 8/10 (uma fatura), 20 (outra), 30 (débitos fixos). Isso é ritmo de
**cobrança**, não de consumo. A data real da compra simplesmente não está no export.

Consequência: nenhum dos dois eixos responde "quando ele gastou". `Vencimento` responde
"quando o dinheiro sai da conta", que é a pergunta de caixa — e é a única respondível.

## Como detectar

```bash
# lote de digitação: quantas linhas compartilham o mesmo timestamp
cut -d, -f4 export.csv | sort | uniq -c | sort -rn | head
```

Mais de uma dezena no mesmo minuto significa importação, e `Lançamento` está queimado
como eixo. Confirmação cruzada: se o gasto diário se concentra em 3–4 dias do mês
repetidos todo mês, esses dias são vencimentos de fatura.

## O que fazer

- Eixo do tempo = `Vencimento`. Declarar isso no relatório, não em rodapé.
- `Efetivação` vazia = previsto, não realizado — separar visualmente e **declarar o
  denominador** (num corte em 19/09, setembro tinha 78 de 179 lançamentos efetivados).
- Um calendário de gasto diário deve dizer na legenda que mostra cobrança, senão o leitor
  conclui que "gasta tudo no dia 20".

## Conexões

- [[Renda Estável com Extraordinário Mascarando Déficit]]
- [[Proveniência como Dado de Primeira Classe]] — cada número do relatório declara de qual
  coluna saiu; é o que torna essa armadilha auditável em vez de invisível.
- [[Finanças Pessoais]]
