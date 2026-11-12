---
title: "Harness2 + flows: transporte Traycer compartilhado"
type: permanent
created: 2026-11-10T14:05:33
moc: "Design de Interface com Agente"
tags: [artifacts, harness2, traycer]
source_inbox: "e267a7d5-harness2-flows-transporte-traycer-compartilhado.md"
tier: "L3"
score: 0.764
---

# Harness2 + flows: transporte Traycer compartilhado

Adaptação do CLI traycer (T3) como biblioteca run_child com mapa run_id->agentId, reutilizada pelo TraycerProposer do Harness2. Fim de fase por polling de agent list/transcript, pois traycer monitor falha em shell limpo. Estudo parado até o v1 fechar; ver artifact harness2-integracao-parked.

# Harness2 + flows: transporte Traycer compartilhado

## Contexto
O projeto artifacts está focado na integração e otimização do Harness2 com o Traycer. A adaptação do CLI traycer (T3) como biblioteca run_child é uma decisão tomada para reutilizar o TraycerProposer do Harness2.

## Detalhes
- **Adaptação do CLI traycer (T3)**: O CLI traycer foi adaptado como uma biblioteca run_child, utilizando um mapa run_id->agentId. Esta abordagem permite a reutilização do TraycerProposer do Harness2.
- **Fim de fase por polling**: A fase atual foi encerrada devido à falha do traycer monitor em shell limpo. O uso de polling para agent list/transcript não é considerado uma solução eficiente.
- **Estudo parado**: O estudo sobre este tópico foi interrompido até que o v1 do Harness2 seja fechado. O artifact harness2-integracao-parked contém informações adicionais sobre o estado atual do estudo.

## Próximos passos
- Reavaliar a abordagem de polling para agent list/transcript.
- Investigar soluções alternativas para monitoramento do traycer.
- Continuar o estudo após o fechamento do v1 do Harness2.

## Conexões
- [[Design de Interface com Agente]]
