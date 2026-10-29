---
title: llama.cpp para Blackwell no WSL2 - Toolkit do Repo wsl-ubuntu e 120a-real
type: pattern
tags: [llama-cpp, cuda, blackwell, wsl2, build, sm120, rtx5050]
created: 2026-10-29
provenance: dotfiles
project: dotfiles
verified: 2026-10-29 via artifacts da epic (review do build em 2026-10-28: 146 ELFs sm_120a, --version dos 4 binários, flags presentes); não recompilado hoje
confidence: low
seen_in: [dotfiles]
---

# llama.cpp para Blackwell no WSL2 - Toolkit do Repo wsl-ubuntu e 120a-real

- **Toolkit:** o `nvidia-cuda-toolkit` do apt do Ubuntu 24.04 é CUDA 12.0 e não tem alvo `sm_120`. Use o repositório `wsl-ubuntu` da NVIDIA e instale **só** o toolkit (>= 12.8). Nunca instale `cuda` nem `cuda-drivers`: puxam driver e sobrescrevem `/usr/lib/wsl/lib/libcuda.so`.
- **Arquitetura:** `-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=120a-real`. O projeto já faz `list(APPEND CMAKE_CUDA_ARCHITECTURES 120a-real)` (`ggml/src/ggml-cuda/CMakeLists.txt:64`); `120` simples não é o que ele usa. Pode omitir a variável. O mecanismo exato do sufixo `a` não foi verificado (uma fonte diz o contrário para `sm_121`). Para PyTorch/CUTLASS o equivalente é `TORCH_CUDA_ARCH_LIST=12.0a`.
- **Verificação do build (`ac8e169`, CUDA 12.8.93):** `libggml-cuda.so` com 146 ELFs `sm_120a`; `libcuda.so.1` vem de `/usr/lib/wsl/lib`; `llama-bench`, `llama-cli`, `llama-server`, `llama-quantize` respondem `--version`; `--n-cpu-moe` e `--cpu-moe` existem.
- **Instalação local sem root:** CUDA em `~/.local/cuda-12.8`, fonte em `~/.local/src/llama.cpp`, binários em `~/.local/bin`. Use `ccache` e limite os jobs (padrão 8).
- **Bench de sanidade:** `llama-bench -p 512 -n 128 -ngl 99 -r 3`. `qwen3 8B Q4_K_M`: `pp512` 1624 ± 58, `tg128` 39,7 ± 1,3 tok/s.
- **Risco aberto:** falha de `ptxas` ao compilar instâncias MXFP4 para `sm_120` (issue llama.cpp #19662). Compile e leia os erros do `ptxas` antes de confiar. O build não falhou, mas **nenhum modelo MXFP4/NVFP4 foi rodado** para provar os kernels.

## O que NÃO funcionou
- Uma preparação dizia que faltava `nvcc`: o autor olhou `/usr/local/cuda` e `~/src`, e o toolkit estava em `~/.local/cuda-12.8`. Procure o `nvcc` real (`command -v`, `~/.local`) antes de concluir que falta.
- Plano original com `CMAKE_CUDA_ARCHITECTURES="120"` e toolkit do apt: corrigido no review antes de compilar.

## 🔗 Conexões
- [[MoE em GPU de 8 GB - Offload de Experts com llama.cpp]]
- [[Plano de Energia Alto Desempenho do Windows Crava a GPU do Notebook em 35 W]]
