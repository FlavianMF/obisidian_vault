---
title: MoE em GPU de 8 GB - Offload de Experts com llama.cpp
type: pattern
tags: [llm, moe, llama-cpp, vram, blackwell, offload, ollama, rtx5050]
created: 2026-10-28
provenance: ollama-8gb-configs
project: ollama-8gb-configs
verified: 2026-10-28 via busca web (existência de Qwen3.6-35B-A3B e Gemma 4 26B-A4B) e GitHub API (PRs #15077, #22196, #29887, #30112 mesclados; issues Ollama #11772, #16515, #17557 abertas). tok/s da pesquisa NÃO verificados e nada de MoE medido na máquina
confidence: low
seen_in: [ollama-8gb-configs]
---

# MoE em GPU de 8 GB - Offload de Experts com llama.cpp

Em MoE, a atenção roda para todo token e os experts (>75% dos pesos) só em parte. Deixe a atenção e o KV na VRAM e mande os experts para a RAM.

- **Flags:** `--n-cpu-moe N` (experts das N primeiras camadas na CPU) e `--cpu-moe` (todos). Verificado: PR llama.cpp #15077, 2025-08-04. Cache de experts em VRAM: PRs #29887 e #30112 (2026-10), nome da flag a confirmar no `--help`.
- **Ollama não faz isso:** divide por camada inteira. Pedidos de offload de experts seguem abertos (#11772, #16515, #17557). MoE maior que a VRAM exige `llama-server`.
- **Ponto de partida (não medido):** gpt-oss-20b MXFP4 `--n-cpu-moe 12-14`; DeepSeek-Coder-V2-Lite Q4_K_M `12`; Qwen3-30B-A3B `30-36`. Ajuste de 2 em 2 até sobrar ~300 MiB de VRAM. Mixtral 8x7B não serve (2-6 tok/s publicados).
- **Blackwell:** NVFP4 nativo desde o PR #22196 (2026-04-28). Compile com `-DCMAKE_CUDA_ARCHITECTURES=120a-real`. Ganho de prefill de 35-65% citado pela pesquisa, não verificado.
- **Armadilha:** Sysmem Fallback do driver NVIDIA faz o estouro de VRAM virar ~1 tok/s sem erro. Configure "Prefer No Sysmem Fallback".
- **Tool calling:** passe `--jinja`; evite quant abaixo de Q4. A pesquisa sugere KV `q4_0`, mas o setup mede com `q8_0`; comece em `q8_0`.
- **Ranking (estimado, 2026-10-28):** Qwen3.6-35B-A3B (3B ativos, SWE-bench Verified 73,4% com scaffold interno, ~18-25 tok/s) > gpt-oss-20b > Gemma 4 26B-A4B > DeepSeek-Coder-V2-Lite (mais rápido, ~28-38 tok/s) > Granite 4 H-Small. Todos os tok/s são estimativas da pesquisa.
- **Gargalo de RAM:** o `.wslconfig` limita o WSL2 a 20 GB e o Qwen3.6 Q4 pesa ~21,5 GB. Suba `memory` para 24 GB ou rode no Windows.
- **Teto de banda:** 3B ativos a ~4,5 bits leem ~1,7 GB por token. Com DDR5 a ~70 GB/s o teto é ~40 tok/s.
- **Origem dos números:** pesquisa do `gemini-3.8-flash` com IDs de arXiv incompletos. Meça antes de confiar: `llama-bench -p 512 -n 128 -ngl 99 --n-cpu-moe N -fa 1`.

## O que NÃO funcionou
- Nada foi executado: o `llama.cpp` não está compilado no WSL e nenhum MoE foi medido nesta máquina. Esta nota vem de leitura de PRs/issues e de uma pesquisa de terceiros.
- Ollama: sem offload de experts, então `qwen3.8` 27B roda por split de camadas (3-6 tok/s estimados) em vez de por experts.
- Mixtral 8x7B: descartado pelos 2-6 tok/s publicados (não verificado).

## 🔗 Conexões
- [[Orçamento de VRAM para LLM Local - Pesos, Grafo e KV Cache]]
- [[opencode com Modelo Local Único Residente em GPU de 8 GB]]
- [[Memória Compartilhada da GPU - CPU Vence no Decode]]
- [[ollama-8gb-configs|Projeto ollama-8gb-configs]]
