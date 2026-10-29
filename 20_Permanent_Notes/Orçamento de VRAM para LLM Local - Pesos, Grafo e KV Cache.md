---
title: Orçamento de VRAM para LLM Local - Pesos, Grafo e KV Cache
type: pattern
tags: [ollama, llm, vram, kv-cache, quantization, gpu, num_ctx]
created: 2026-10-15
provenance: ollama-8gb-configs
project: ollama-8gb-configs
verified: 2026-10-15 via leitura dos docs/Modelfiles do repo (estimativas, nada medido na máquina). 2026-10-29 via artifact de execução da epic (medição de 2026-10-28 com qwen3:8b; não reproduzido hoje)
confidence: low
seen_in: [ollama-8gb-configs, dotfiles]
---

# Orçamento de VRAM para LLM Local - Pesos, Grafo e KV Cache

Como decidir se um modelo cabe 100% na GPU e qual `num_ctx` usar, antes de baixar.

## Fórmula

```text
VRAM livre − pesos − projetor de visão (se houver) − ~0,6-0,7 GiB de grafo − KV cache(num_ctx) − margem ~0,3 ≥ 0
KV por token = 2 × camadas COM atenção × KV heads × head_dim × bytes   (f16=2, q8_0≈1,06)
```

- "VRAM livre" é a que o log do Ollama reporta (`available`), não o total: 8 GB nominais → ~6,9 GiB.
- Modelos **híbridos** (Qwen3.5/3.8: `full_attention_interval 4`; Granite 4 `-h`: Mamba-2; Gemma 4: janela deslizante) só contam as camadas de atenção completa. Qwen3.5-4B: 8 de 32 camadas → ~17 KiB/token em q8_0, contra ~76 KiB num denso 8B. O contexto deixa de ser o gargalo.
- Modelo denso tradicional: contexto é o controle principal de VRAM.
- Geometria real: `ollama show --verbose <modelo>`; tamanho: `ollama list`.

## Teto de velocidade

Decode é limitado por memória: `tok/s ≈ largura de banda ÷ bytes lidos por token`. MoE conta só os parâmetros ativos (Granite 4 tiny-h ~1B ativo = teto altíssimo). Fonte de largura de banda divergente (RTX 5050 Laptop: 224 vs 384 GB/s), então reporte faixa, nunca número único.

## Passos práticos

1. Servidor: `OLLAMA_FLASH_ATTENTION=1` + `OLLAMA_KV_CACHE_TYPE=q8_0` (sem flash attention o KV quantizado não vale), `NUM_PARALLEL=1`, `MAX_LOADED_MODELS=1`.
2. `num_ctx` por modelo num Modelfile (`FROM x` + `PARAMETER num_ctx N`), nome `<x>-capella`; vence o `OLLAMA_CONTEXT_LENGTH` global. Ver [[Ollama Ignora Tamanho de Contexto Enviado por Request]].
3. Validar: `ollama ps` → PROCESSOR `100% GPU` e CONTEXT igual ao Modelfile.

## Medido (2026-10-28, qwen3:8b Q4_K_M, Ollama 0.40.11, FA + KV q8_0)

| `num_ctx` | Camadas na GPU | VRAM usada | Decode |
| --- | --- | --- | --- |
| 16384 | 37/37 | 7517 MiB (4643,78 pesos + 1224 KV + 112 compute), 394 MiB livres | 41,27 tok/s |
| 24576 | 33/37 | KV sobe para 1836 MiB | 19,14 tok/s |

Quatro camadas na CPU cortam o decode pela metade. O limite de 8 GB está entre 16K e 24K para esse modelo. Fonte: artifact de execução da epic dotfiles; não reproduzido hoje.

## Ressalva

Os números do projeto de origem (`ollama-8gb-configs`) são **estimativas**; as tabelas de medição dele (eval rate, PROCESSOR) ficaram vazias. A única medição é a da seção acima, num modelo (`qwen3:8b`). Trate o resto como método, não como resultado.

## 🔗 Conexões
- [[ollama-8gb-configs|Projeto ollama-8gb-configs]]
- [[Tag Multimodal do Ollama Carrega Projetor de Visão e Estoura a VRAM]]
- [[Ollama Ignora Tamanho de Contexto Enviado por Request]]
