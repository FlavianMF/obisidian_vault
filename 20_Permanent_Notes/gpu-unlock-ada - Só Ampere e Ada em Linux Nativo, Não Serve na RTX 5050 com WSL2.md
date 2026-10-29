---
title: gpu-unlock-ada - Só Ampere e Ada em Linux Nativo, Não Serve na RTX 5050 com WSL2
type: concept
tags: [gpu, tensor-cores, blackwell, ada, wsl2, nvidia, llm]
created: 2026-10-29
provenance: dotfiles
project: dotfiles
verified: 2026-10-29 via artifact de pesquisa (leitura do repo e de fontes); nada executado na máquina
confidence: low
seen_in: [dotfiles]
---

# gpu-unlock-ada - Só Ampere e Ada em Linux Nativo, Não Serve na RTX 5050 com WSL2

`JustAResearcher/gpu-unlock-ada` remove o corte de 50% na taxa de emissão dos Tensor Cores em GeForce quando o acumulador é FP32 (FP16/BF16/TF32/FP8 → FP32). Em RTX 4090: 165,6 → 331,6 TF/s (FP16→FP32). INT8 e FP32 escalar não mudam.

- **Ganho real é menor:** +12% a +55% em cuBLAS GEMM, porque o teto de potência chega antes. **Inferência INT4/INT8 sem acumulação FP32 quase não ganha.**
- **Como funciona:** corrupção de pilha no `booter_load` do SEC2 durante o cold boot (initramfs, antes do driver) abre `FEAT_OVR_PLM` e grava `SS0/SS1`; o override sobrevive ao FLR.
- **Por que não serve aqui (3 barreiras):** (1) Blackwell eliminou `booter_load` e usa FSP + FMC: sem desbloqueio conhecido para a série 50, e a limitação (`fmla32 = 3`) continua; (2) exige Linux nativo ou VFIO, não WSL2; (3) exige driver carregado após o initramfs. O setup é GB207M (`10de:2d98`), VBIOS `98.07.27.00.11`.
- **Conclusão para LLM local:** não gaste tempo aqui. O ganho vem de energia (ver [[Plano de Energia Alto Desempenho do Windows Crava a GPU do Notebook em 35 W]]) e de offload de experts.

## 🔗 Conexões
- [[MoE em GPU de 8 GB - Offload de Experts com llama.cpp]]
