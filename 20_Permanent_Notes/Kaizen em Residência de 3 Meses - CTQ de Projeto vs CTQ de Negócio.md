---
title: Kaizen em Residência de 3 Meses - CTQ de Projeto vs CTQ de Negócio
type: pattern
tags: [kaizen, residencia, pnaat, ctq, baseline, pme, iot, visao-computacional, project-methodology]
created: 2026-10-23
provenance: residencia_cariri_projects
seen_in: [residencia_cariri_projects]
scope: project
verified: 2026-10-23 via leitura dos 8 decks "Review de escopo" de 16/10/2026 e pesquisa web (fontes nas notas ligadas)
confidence: low
---

# Kaizen em residência de 3 meses — CTQ de projeto vs CTQ de negócio

Contexto: residência **PNAAT** no Cariri (CE). O PNAAT tem apoio do MCTI com recursos da Lei
de Informática, no programa MCTI Futuro com a Softex; o FIT hospeda a página. Residência de
3 meses, 4 h/dia, 4 alunos por empresa, 8 PMEs. Cada time apresenta à empresa um deck
"Kaizen" nas reviews (escopo na semana 2, depois reviews mensais e a final). Guia prático no
repo: `residencia_cariri_projects/Gestao/metodo/kaizen-review.md`.

## Padrão

**Separe dois níveis de CTQ e diga à empresa qual nível o projeto promete mover.**

| Nível | O que mede | Exemplo | Compromisso em 12 semanas |
|---|---|---|---|
| CTQ de projeto | O fluxo de dado ou o processo que o time constrói | % de paradas registradas com motivo; latência até o painel; acurácia da contagem | Meta com valor e data |
| CTQ de negócio | O efeito na operação | OEE; peças por hora-homem; perda %; R$ | Baseline + tendência, sem meta garantida |

Mais **uma medida de equilíbrio** (ex.: tempo de apontamento do operador). Ver
[[CTQ - Definição Operacional, Baseline e Medida de Equilíbrio]].

## Cronograma que cabe em 3 meses

1. **Semanas 1–3**: glossário dos termos (o que é parada, refugo, turno planejado);
   baseline manual, por método independente do sistema novo; foto do "antes".
2. **Semanas 4–8**: construir e rodar **em paralelo** ao registro atual.
3. **Semanas 9–12**: operar, medir, comparar com o mesmo mix de produtos e turnos.
4. **Antes de sair**: plano de controle com dono na empresa e datas de 30/60/90 dias. Ver
   [[Sustentação de Ganhos de Kaizen - O que a Pesquisa Mostra]].

## Checklist "pronto para review"

- [ ] Problema escrito como lacuna medida, sem a solução embutida e sem culpado.
- [ ] Sponsor e **dono do processo** na empresa nomeados (nome e cargo).
- [ ] Cada CTQ com definição operacional, unidade, método, baseline (período e n), meta e
      prazo; ≥ 1 medida de equilíbrio.
- [ ] Baseline coletado antes da intervenção, por método independente da solução.
- [ ] Causas do Ishikawa marcadas como hipótese / verificada / descartada; 5 Porquês com
      evidência e teste "portanto".
- [ ] Contramedida (o P1) ligada a uma causa, com previsão numérica do efeito.
- [ ] Requisitos com prioridade e critério de aceite.
- [ ] Plano de ação com dono único e data por linha; atrasados destacados.
- [ ] Compras com decisão de quem compra e prazo de aprovação.
- [ ] Fotos antes/depois do mesmo ângulo; run chart com a data da mudança.
- [ ] Plano de controle: padrão, frequência, reação, dono, datas de 30/60/90 dias.

## Riscos por tipo de projeto

- **Visão computacional (contagem)**: a referência é contagem dupla independente ou vídeo
  revisado quadro a quadro, porque o humano também erra. Lotes estratificados por turno,
  iluminação, modelo e oclusão. Métricas: erro % por lote, viés, limites de Bland-Altman.
  Meta fixada antes do teste.
- **ESP32 + MQTT (paradas)**: limiar de "parado" escrito e validado contra observação;
  buffer offline; QoS adequado; relógio por NTP. O **motivo** da parada continua com o
  operador.
- **OEE em linha manual** (calçado, confecção): OEE de equipamento informa pouco; prefira
  pares por hora-homem e aderência ao takt. Ver
  [[OEE - Fórmula, Seis Grandes Perdas e Armadilhas de Medição]].
- **Peltier para resfriar rack**: COP baixo (~0,36 num experimento; eficiência exergética
  ~24% contra ~59% da compressão). Medir temperatura de entrada do equipamento **e** W
  consumidos; risco de condensação [incerto].
- **Solar × consumo × fatura**: o medidor bidirecional só vê o que vem da rede e o que é
  injetado; o **autoconsumo instantâneo não aparece na fatura**. Medir no inversor ou por TC.
  Lei 14.300/2022 e REN ANEEL 1.059/2023: créditos valem 60 meses; quem entrou depois de
  06/01/2023 paga Fio B escalonado (60% em 2026). Ciclo de leitura ≠ mês civil.

## O que NÃO funcionou

Observado nos 8 decks "Review de escopo" de 16/10/2026 (semana 2):
- **Solução antes do problema**: 5 dos 8 decks não têm Ishikawa nem 5 Porquês; o objetivo
  já é a tecnologia (tablet, totem, câmera, sensor). Nos 3 que têm, os campos estão vazios.
- **CTQ sem baseline nem método**: todos com início "a medir" e meta "a definir", sem
  definição operacional. O "Registro do antes" do template lista só 2 dos 3 CTQs.
- **Sem dono na empresa**: 2 decks com responsável "a confirmar"; nenhum nomeia sponsor nem
  dono do processo; épicos e ações sem responsável.
- **CTQs de adoção no lugar de efeito**: alguns medem só se a ferramenta é usada (% de
  turnos com apontamento digital), sem nenhum CTQ de negócio para dar sentido.

## Ligações

[[Lean Antes de Digitalizar - Lean 4.0 e Desperdício Digital]] ·
[[Brasil Mais Produtivo - Lean em PMEs com Indicador Único por Linha]] ·
[[A3 - Relatório de Uma Página Como História PDCA]] ·
[[Scrum Enxuto para Residência com Alunos em Tempo Parcial]].
Mapa: [[Kaizen e Melhoria Contínua]].

## Fontes

- FIT/MCTI/Softex, página PNAAT, 2026 — https://fit-tecnologia.org.br/pnaat
- Termoelétrico, eficiência — https://en.wikipedia.org/wiki/Thermoelectric_heat_pump
- Canal Solar, Fio B 2026 — https://canalsolar.com.br/consumidores-60-do-fio-b-2026/
- Migalhas, Lei 14.300 — https://www.migalhas.com.br/depeso/365692/mas-afinal-o-que-muda-com-o-marco-legal-da-geracao-distribuida
- ANEEL REN 1.059/2023 — https://www.lex.com.br/resolucao-normativa-aneel-no-1-059-de-7-de-fevereiro-de-2023/
- Xavier et al., contagem por YOLOv5, ICCSA 2022 — https://bv.fapesp.br/pt/publicacao/222536
