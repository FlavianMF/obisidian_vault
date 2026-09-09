---
title: TDD em Firmware ESP-IDF via test_apps
type: pattern
tags: [esp-idf, tdd, embedded, unity, testing, agentic-ai]
created: 2026-09-09
provenance: webnar_iot_genai
---

# TDD em Firmware ESP-IDF via test_apps

## Padrão

Pra aplicar TDD em firmware embarcado (ESP-IDF) sem inventar mocks de
hardware:

1. **Isolar lógica pura** (sem depender de display/wifi/GPIO) em funções
   próprias dentro do componente `main` (ex: conversão/formatação de dado,
   parsing, cálculo) — separado do bring-up de hardware.
2. Criar um **app de teste separado** em `test_apps/<component>/`, seguindo
   o padrão oficial da Espressif (`test_apps/<component>`): projeto ESP-IDF
   próprio, com `EXTRA_COMPONENT_DIRS` apontando pro componente real sendo
   testado, usando o framework **Unity** (já embutido no ESP-IDF).
3. Rodar no hardware real: `idf.py -C test_apps/<component> build flash
   monitor` — imprime `PASS`/`FAIL` no monitor serial.

## Por que funciona bem com IA generativa / live-coding

Ciclo red-green fica totalmente demonstrável em hardware real e observável
via serial (canal que já é natural em projetos embarcados) — sem precisar
de host-side testing framework separado. Bom pra demos ao vivo: pedir pra
IA escrever o teste primeiro (falha/não compila), depois implementar até
passar, é um ciclo curto e visualmente claro no monitor serial.

## Quando usar

Projetos ESP-IDF onde a plateia/equipe já observa o monitor serial mesmo
(debug, logs) — reaproveita o mesmo canal pro output de teste, em vez de
introduzir uma ferramenta de teste host-side separada.

## Conexões

- [[Checklist de Bootstrap de Workflow de Desenvolvimento]]
- [[IA Generativa na Engenharia de Sistemas]]
