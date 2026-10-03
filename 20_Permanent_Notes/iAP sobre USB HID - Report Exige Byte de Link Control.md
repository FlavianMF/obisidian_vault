---
title: iAP sobre USB HID — Report Exige Byte de Link Control
type: trap
tags: [ipod, iap, usb-hid, tinyusb, esp32, protocolo, car-radio, kenwood]
created: 2026-10-03
provenance: ipod_uart_simulator
project: ipod_uart_simulator
seen_in: [ipod_uart_simulator]
verified: 2026-10-03 via oandrew/ipod hid/hid.go + log de bancada KVT-512
confidence: medium
---

# iAP sobre USB HID — Report Exige Byte de Link Control

Ao emular um iPod (iAP1) como gadget USB HID para um rádio automotivo, **cada
report HID não carrega o frame iAP cru**. Layout real (oandrew/ipod-gadget):

```
report = [report_id][link_control][dados ... padding 0x00 até o tamanho do report]
link_control: 0x00 único/último | 0x01 continuação | 0x02 há mais a seguir | 0x03 meio
iPod -> rádio (Input):  IDs 0x01..0x04, len 12/14/20/63 (len inclui o link byte)
rádio -> iPod (Output, via SET_REPORT): IDs 0x05..0x09, len 8/10/14/20/63
```

O iPod escolhe o **menor report que caiba** o restante do frame; frame grande
(certificado de auth, IDPS) vira vários reports encadeados pelo link byte.

## Sintoma

Rádio (Kenwood KVT-512) manda `Identify(0x00)` + `RequestLingoVersion(0x00)`,
o simulador responde `ReturnLingoVersion` e **o rádio fica mudo para sempre**,
tela presa em "reading". Nenhum erro em lado nenhum.

## Por quê

Sem o link byte, o rádio lê o `0x55` (start byte do frame) como link_control:
bit0 = continuação de um frame que nunca começou → descarta. Toda resposta do
iPod se perde. No sentido inverso o bug fica escondido: o report do rádio começa
com `0x00` (link "único") e um parser que pula bytes até `0x55` "funciona" por
sorte — até chegar um frame maior que um report.

## Armadilha secundária: simulador de teste simétrico

O simulador do rádio em Python tinha **o mesmo erro de framing** que o firmware,
então a bancada PC↔ESP32 passava. Harness de teste escrito pelo mesmo autor do
DUT replica a mesma leitura errada do protocolo. Ancore o framing num código de
referência externo (aqui `oandrew/ipod hid/hid.go`, `report_def.go`) e teste os
dois lados contra vetores dele, não um contra o outro.

## Como aplicar

- Isolar a camada de link num módulo puro (encoder/decoder) testável no host.
- Decoder: remontar por link byte e cortar o padding **pelo campo LEN do frame
  iAP**, não por "zeros no fim" (checksum pode ser `0x00`).
- Logar checksum inválido / frame órfão — falha silenciosa foi o que escondeu
  isto.
- Dump hex dos reports crus com toggle no console para bancada.

Relacionado: no iAP o **iPod autentica o acessório** (envia 0x14/0x16/0x17/0x19;
acessório responde 0x15/0x18) — fácil inverter os papéis lendo só os nomes.
