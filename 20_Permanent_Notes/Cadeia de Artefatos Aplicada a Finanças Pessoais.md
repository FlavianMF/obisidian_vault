---
title: Cadeia de Artefatos Aplicada a Finanças Pessoais
type: pattern
tags: [project-methodology, financas-pessoais, prd, plano-de-fase, aceite, trade-off, v-and-v]
created: 2026-09-19
provenance: budget_report
---

# Cadeia de Artefatos Aplicada a Finanças Pessoais

Terceira aplicação da [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]]
fora de software, ao lado de
[[Cadeia de Artefatos Aplicada a Projeto de Conteúdo e Marca]]. Domínio: orçamento
doméstico em déficit, com quatro meses de extrato como única base factual.

A origem fecha o círculo — a cadeia foi destilada do `orbita-platform`, que é uma
plataforma financeira. Aqui ela volta ao domínio, sem o software no meio.

## Nível e mapeamento

**Nível 2**: entrega única (um relatório), mas com decisões que vão ser redebatidas.
Sem RFC-000, sem cadeia de nove artefatos.

| Peça da cadeia | No orçamento doméstico |
|---|---|
| Intenção | "entender o que houve com as contas e montar um plano de melhoria" |
| Escopo / PRD | o que o dado cobre (jun–set/2026, dois CSV) e o que ele **não** sabe |
| Decisão técnica | o trade study de onde cortar, com pesos e sensibilidade |
| Plano de fase | `E0..E6`, cada etapa executável e verificável sozinha |
| Nota de conclusão | o export do mês seguinte, lido contra o aceite |
| Playbook | as armadilhas financeiras já pagas, append-only |

## As quatro transposições que valem a viagem

**1. `E0` é higienização, não economia.** A etapa de fundação não muda o caixa: atribui
conta às despesas órfãs, corrige categoria errada, fixa a convenção de divisão entre o
casal. É a única etapa onde uma regressão é fácil de atribuir — e meta calculada sobre
dado sujo não é verificável. Num caso real, 2.000 de devolução de benefício e um posto de
combustível estavam dentro de `Alimentação / Lanche`; qualquer meta de "gastar menos com
comida" nasceria furada.

**2. Aceite como teste negativo funciona melhor aqui do que meta percentual.**
"Reduzir 20% dos gastos" não reprova ninguém: sempre há um mês atípico para explicar.
O aceite que reprova é declarativo e checável no CSV:

- "variável de nov/26 acima de 5.000 reprova";
- "qualquer lançamento com `Recorrência = Parcelada` e `Parcela = 1` vencendo após
  01/11/2026, fora da lista de exceções escrita antes, reprova";
- "fatura com vencimento em 20/12/2026 acima de 6.000 reprova".

A diferença prática: o percentual convida à negociação no fim do mês; o teste negativo já
foi negociado no começo.

**3. "Etapa mesclável" vira "executável e verificável sozinha".** Sem git, o critério de
corte é o mesmo: se a etapa precisa de outra para produzir um efeito observável no
extrato, está mal cortada. E o diagrama de dependências mostra o que é paralelizável —
no caso, congelar novo parcelamento não depende de nada e pode começar no mesmo dia.

**4. Matriz de V&V com o export do mês seguinte como instrumento.** Cada requisito ganha
método (I/A/D/T) e um critério que se resolve por filtro no CSV. É o equivalente doméstico
de "rodar a suíte": não há opinião envolvida na verificação.

## O que **não** transpõe

Não existe worktree nem PR, então a relação 1:1:1:1 (etapa/branch/PR/nota) perde uma
perna. O substituto é o ciclo mensal: um export por mês faz o papel do merge, e a leitura
do aceite contra ele faz o papel da revisão. Mais lento e menos granular — fatiar uma
etapa não acelera a verificação, porque a cadência é do calendário, não sua.

## Conexões

- [[Plano de Fase em Etapas Mescláveis]] — de onde vêm `E0`, `En` e o aceite negativo.
- [[Análise de Trade-off (Trade Study)]] — os 8 passos, com a análise de sensibilidade
  como o teste de robustez da decisão.
- [[Matriz de V&V - Birthday Counter]] · [[Registro de Riscos - Birthday Counter]]
- [[Playbook de Projeto - Erros Já Cometidos Como Artefato]]
- [[Renda Estável com Extraordinário Mascarando Déficit]] — o diagnóstico que esta cadeia
  organizou.
- [[Finanças Pessoais]]
