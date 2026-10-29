---
title: Plano de Energia Alto Desempenho do Windows Crava a GPU do Notebook em 35 W
type: trap
tags: [llm, gpu, rtx5050, lenovo, dynamic-boost, windows, performance, wsl2]
created: 2026-10-29
provenance: dotfiles
project: dotfiles
verified: 2026-10-29 via artifact de execução da epic (medições de 2026-10-28 com nvidia-smi: clocks.mem, clocks.sm, pstate, power.draw); não reproduzido hoje
confidence: low
seen_in: [dotfiles]
---

# Plano de Energia Alto Desempenho do Windows Crava a GPU do Notebook em 35 W

Em notebook Lenovo LOQ (i7-13650HX + RTX 5050 8 GB), o plano "Alto Desempenho" do Windows **reduz** o decode de LLM. Use plano **Equilibrado** + modo térmico Performance da Lenovo.

- **Causa:** no Alto Desempenho a CPU trava os clocks no máximo. O Dynamic Boost (Intel IPF + NVIDIA) tira a margem dinâmica da GPU e a deixa no `Default Power Limit` de 35 W. A GDDR7 fica em 9001 MHz (P4).
- **Correção:** plano Equilibrado + `SmartFanMode = 3` (WMI `LENOVO_GAMEZONE_DATA`) + `Dynamic Boost = 15 W` (ID `0x02010300`, `LENOVO_OTHER_METHOD`). A GPU passa a 45-53 W, sobe para P2 (GDDR7 11001 MHz, SM 1700-2000 MHz).
- **Medido (`qwen3:8b` Q4_K_M, 37/37 camadas):** decode 22,43 tok/s (frio) / 33,91 (cap 35 W) → 37,66-41,27 tok/s. Potência 34,8 W → 45,1 W média, 52,8 W pico.
- **Travar a memória não ajuda:** `nvidia-smi -lmc 12001,12001` gasta 6-8 W a mais no mesmo orçamento. Com 35 W o SM caiu para 352-650 MHz e o decode para 23,80 tok/s. Com 45 W, 32,54-34,11 tok/s, abaixo do boost automático. Mantenha `-rgc` e `-rmc`.
- **TGP não é constante do modo:** li 46,86 W em repouso e 51,95 W de pico no mesmo modo. Reporte média e pico sob carga. `nvidia-smi -pl` é rejeitado em notebook e o `nvidia-smi` do WSL2 não escreve na placa: o caminho é o EC.
- **Contador não confiável:** `SW Power Capping` e `SW Thermal Slowdown` leem o mesmo número no `nvidia-smi` do WSL2. Prove limitação com clock e potência, não com esse contador.
- A leitura WMI da Lenovo dá "Acesso negado" sem Admin.

## O que NÃO funcionou
- Plano Alto Desempenho do Windows: piorou (35 W fixos).
- Travar GDDR7 em 12001 MHz: piorou nos dois orçamentos de energia testados.
- Usar `SW Power Capping` como evidência: o contador espelha outro campo.
- Não testado: outras máquinas. O comportamento do EC vale para o modelo `83UX`.

## 🔗 Conexões
- [[Orçamento de VRAM para LLM Local - Pesos, Grafo e KV Cache]]
- [[Memória Compartilhada da GPU - CPU Vence no Decode]]
