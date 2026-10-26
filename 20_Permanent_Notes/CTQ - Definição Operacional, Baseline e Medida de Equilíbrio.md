---
title: CTQ - Definição Operacional, Baseline e Medida de Equilíbrio
type: concept
tags: [kaizen, ctq, six-sigma, metricas, baseline, run-chart, kpi, measurement]
created: 2026-10-23
provenance: residencia_cariri_projects
seen_in: [residencia_cariri_projects]
verified: 2026-10-23 via pesquisa web (iSixSigma 2025, IHI, Provost & Murray, Locke & Latham 2002, Farris 2006; fontes na nota)
confidence: low
---

# CTQ — definição operacional, baseline e medida de equilíbrio

## Origem

**CTQ (Critical to Quality)** vem do Six Sigma: atributo mensurável que o cliente considera
importante (iSixSigma, 2025). A **árvore de CTQ** desdobra a voz do cliente (VOC) em
necessidade → driver → requisito mensurável.

## Campos de um CTQ bem escrito

| Campo | Exemplo |
|---|---|
| Nome | Tempo até o dado de produção chegar à gestão |
| Definição operacional | Do fim do turno até o número aparecer no painel do PCP |
| Unidade | horas |
| Método e instrumento | Registro do horário em 20 turnos (papel hoje, log do sistema depois) |
| Frequência e amostra | 1 medida por turno |
| Responsável pela coleta | Nome de uma pessoa |
| Baseline | Valor, período e n |
| Meta e prazo | Valor e data |
| Limite ou especificação | Se houver |

Qualidade abstrata ("pontualidade") precisa virar algo contável. Definição frouxa estraga a
comparação antes/depois (exemplo clássico: Mars Climate Orbiter, unidades diferentes).

## Três tipos de medida (IHI)

- **Resultado**: impacto no cliente ou no negócio. 1 ou 2 por projeto.
- **Processo**: as etapas estão rodando como planejado?
- **Equilíbrio**: a melhoria piorou outra coisa? Exemplo: a câmera reduz o refugo, mas
  aumenta paradas por falso positivo.
- Total recomendado: de 4 a 10 medidas.

## Baseline

- O baseline tem de vir **antes da intervenção** e de um método **independente do sistema
  novo**. O sistema que se quer avaliar não pode criar o próprio baseline.
- Sem sistema na empresa: coleta manual com folha de verificação antes de instalar o sensor.
- IHI: dado suficiente, não perfeito; coleta embutida no trabalho; **amostragem** quando o
  dado completo é caro (ex.: 25 casos por semana por 6 semanas).
- Período mínimo universal: não há [incerto]. Referências práticas: ~10 pontos para a
  mediana de um run chart, ~20 pontos para limites de controle.

## Run chart

IHI chama o gráfico de tendência de "a ferramenta mais poderosa": marcar no gráfico quando
cada mudança entrou. Regras (Perla, Provost & Murray, 2011): **shift** = 6 ou mais pontos
seguidos do mesmo lado da mediana; **trend** = 5 ou mais pontos subindo ou descendo.

## Meta

- SMART (Doran, 1981).
- Locke & Latham (2002): meta difícil porém viável gera mais esforço; meta alta demais
  desmotiva. Farris (2006): a **dificuldade da meta** previu 3 de 5 resultados de eventos
  kaizen.
- A meta não embute a solução nem culpa ninguém.

## Fontes

- Kinney, CTQ, iSixSigma, 2025 — https://isixsigma.com/dictionary/critical-to-quality-ctq
- iSixSigma, Operational definitions — https://www.isixsigma.com/dmaic-methodology/moms-know-all-about-clear-operational-definitions/
- IHI, Establishing Measures — https://www.ihi.org/how-improve-model-improvement-establishing-measures
- Regras de run chart (Provost & Murray, via fonte secundária) — https://mwsug.org/proceedings/2018/HS/MWSUG-2018-HS-71.pdf
- UF IFAS, SMART goals / Locke & Latham — https://edis.ifas.ufl.edu/publication/FE577/pdf
- Farris, tese, Virginia Tech, 2006 — https://vtechworks.lib.vt.edu/items/258d1964-ea74-4885-bba0-e67e05213dca

Ver também [[OEE - Fórmula, Seis Grandes Perdas e Armadilhas de Medição]] e
[[Lean Antes de Digitalizar - Lean 4.0 e Desperdício Digital]] (CTQs de dado).
Mapa: [[Kaizen e Melhoria Contínua]].
