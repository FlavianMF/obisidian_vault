---
title: Memória Compartilhada da GPU - CPU Vence no Decode
type: concept
tags: [ollama, llm, gpu, nvidia, windows, sysmem-fallback, performance, pcie]
created: 2026-10-15
provenance: ollama-8gb-configs
project: ollama-8gb-configs
verified: 2026-10-15 via leitura de shared-memory-study.md (cálculo de largura de banda; teste A/B não executado)
confidence: low
seen_in: [ollama-8gb-configs]
---

# Memória Compartilhada da GPU - CPU Vence no Decode

"Memória compartilhada da GPU" no Windows é RAM comum (até ~metade da RAM) emprestada à GPU via WDDM. Quando o modelo não cabe na VRAM, **deixar as camadas excedentes na CPU é ~2-4× mais rápido** que a GPU lê-las pela RAM via PCIe:

| Caminho | Banda prática estimada |
|---|---|
| CPU → RAM DDR5-4800 2 canais | ~60 GB/s (teórico 76,8) |
| GPU → RAM via PCIe 5.0 x8 | ~25 GB/s (teórico 32); Gen4: ~13 |

Exemplo (27B, 11,5 GB fora da VRAM): CPU ~4-5 tok/s; sysmem ~1-2 tok/s. O Ollama/llama.cpp já faz a divisão certa; o problema é o **fallback silencioso do driver** (NVIDIA ≥536.40) quando a VRAM é superestimada: lentidão enorme sem erro.

## Ação
- NVIDIA Control Panel → `ollama.exe` e `ollama app.exe` → **CUDA - Sysmem Fallback Policy = Prefer No Sysmem Fallback** (driver ≥546.01); reiniciar o Ollama (a política é lida na criação do contexto CUDA). Vira OOM explícito em vez de lentidão.
- Sinal de estouro: vários GB de memória compartilhada subindo durante a geração (poucos centésimos são normais).
- `GGML_CUDA_ENABLE_UNIFIED_MEMORY` é Linux; WSL2 ignora a política. iGPU Intel: descartada pelo Ollama (`dropping integrated GPU`), manter assim.
- Prefill (compute-bound) e MoE (poucos experts ativos por token) são onde a GPU/split ainda compensa.
- Raptor Lake (6P+8E): testar `num_thread` = nº de P-cores contra o padrão quando há CPU no caminho.
- Limitar a VM do WSL2 em `.wslconfig` (`memory=8GB`) para não disputar RAM com o modelo dividido.

Hipótese não confirmada por teste A/B nesta máquina (tabela do estudo vazia).

## 🔗 Conexões
- [[Orçamento de VRAM para LLM Local - Pesos, Grafo e KV Cache]]
- [[Otimização de Recursos para LLMs em CPU]]
- [[Projeto ollama-8gb-configs]]
