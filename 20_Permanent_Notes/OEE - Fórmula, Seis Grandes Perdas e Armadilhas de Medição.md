---
title: OEE - Fórmula, Seis Grandes Perdas e Armadilhas de Medição
type: concept
tags: [oee, tpm, lean, manufacturing, metricas, baseline, iot]
created: 2026-10-23
provenance: residencia_cariri_projects
seen_in: [residencia_cariri_projects]
verified: 2026-10-23 via pesquisa web (Vorne/OEE.com, Nakajima via fontes secundárias, Reliable 2026, estudos de caso; fontes na nota)
confidence: low
---

# OEE — fórmula, seis grandes perdas e armadilhas de medição

## Origem e fórmula

**OEE (Overall Equipment Effectiveness)** vem de Seiichi Nakajima (JIPM), dentro do TPM
(*Introduction to TPM*, 1984; inglês 1988). Definições da Vorne (OEE.com):

- **Tempo planejado** = turno − tempo sem intenção de produzir (intervalos).
- **Tempo de operação** = tempo planejado − paradas.
- **Disponibilidade (A)** = tempo de operação / tempo planejado.
- **Desempenho (P)** = (ciclo ideal × total produzido) / tempo de operação.
- **Qualidade (Q)** = peças boas / total produzido. Retrabalho conta como perda.
- **OEE** = A × P × Q = **peças boas × ciclo ideal / tempo planejado**.
- **TEEP** = OEE × utilização, onde utilização = tempo planejado / tempo total do calendário.

## Seis grandes perdas

| Fator | Perdas |
|---|---|
| Disponibilidade | Quebras; setup e ajustes |
| Desempenho | Pequenas paradas e ociosidade; velocidade reduzida |
| Qualidade | Defeitos e retrabalho; perdas de partida |

## O número de 85%

- Vem de ~90% A × 95% P × 99,9% Q. Nakajima tratava esses valores como mínimos práticos.
- **Crítica (Vorne)**: o número é do Japão dos anos 1970, automotivo, manufatura discreta. A
  maioria das fábricas fica perto de 60%; há mais plantas abaixo de 45% do que acima de 85%.
- Compare a linha **consigo mesma**, não com outras. Meta realista para 3 a 4 meses.
- Estudos de caso em PMEs partem de 50% a 65% (ex.: metalmecânica no Peru 64,9% → 81,2%).
  Não há survey representativo de PMEs [incerto].

## Armadilhas de medição

- **P > 100%** indica ciclo ideal errado.
- **Ciclo ideal**: valor de placa ou melhor demonstrado? Com mix de produtos, um ciclo por
  SKU.
- **Micro-paradas** entram em P; paradas longas, com motivo, entram em A. Não há limiar
  fixo: definir e escrever o limiar.
- **Log manual e ciclo ideal "generoso" inflam o OEE** (Reliable, 2026).
- OEE pode subir enquanto Q cai.
- **Linha manual** (costura, montagem de calçado) não é ditada por máquina: OEE de
  equipamento informa pouco. Preferir peças por hora-homem e aderência ao takt.

## Baseline quando o apontamento é em papel

1. **Glossário congelado antes de medir**: tempo planejado, limiar de parada, ciclo ideal,
   o que é refugo.
2. **OEE simplificado** com o que o papel já tem: peças boas por turno × ciclo ideal /
   tempo planejado. Dá o número, mas não separa A de P.
3. **1 a 2 semanas de observação cronometrada** ou amostragem do trabalho para estimar A e P.
4. **Rodar o sistema digital em paralelo ao papel** e publicar a diferença. Se o OEE "cair"
   com o sistema novo, é efeito de medição (o papel escondia micro-paradas), não piora.

## Fontes

- Vorne, World-class OEE — https://www.oee.com/world-class-oee/
- Vorne, Calculating OEE — https://www.oee.com/calculating-oee/
- Vorne, TEEP — https://www.oee.com/teep/
- Reliable, OEE benchmarks by industry, 2026 — https://reliamag.com/guides/oee-benchmarks-by-industry-what-world-class-really-means/
- Caso OEE em PME no Peru (U. Lima) — https://alicia.concytec.gob.pe/vufind/Record/RULI_1d455a980cfb32fc1335ccf2a206f0e1
- Caso SMED em PME no Vietnã, 2019 — https://jad.hcmuaf.edu.vn/index.php/jadvn/article/download/25/339

Ver também [[CTQ - Definição Operacional, Baseline e Medida de Equilíbrio]].
Mapa: [[Kaizen e Melhoria Contínua]].
