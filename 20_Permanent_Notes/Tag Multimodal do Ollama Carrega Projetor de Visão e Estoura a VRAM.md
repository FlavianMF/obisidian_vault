---
title: Tag Multimodal do Ollama Carrega Projetor de Visão e Estoura a VRAM
type: trap
tags: [ollama, llm, vram, vision, gguf, huggingface, modelfile]
created: 2026-10-15
provenance: ollama-8gb-configs
project: ollama-8gb-configs
verified: 2026-10-15 via leitura do manifesto citado nos docs do repo (import hf.co não testado)
confidence: low
seen_in: [ollama-8gb-configs]
---

# Tag Multimodal do Ollama Carrega Projetor de Visão e Estoura a VRAM

## Sintoma
Modelo "9B Q4" que deveria caber em 8 GB sai com offload parcial para a CPU e o decode cai ~3× (relato de 55 → 17 tok/s com 37/41 camadas na GPU).

## Causa
A tag oficial de modelos multimodais (ex.: `qwen3.5:9b`, `gemma4:e4b`) inclui o **projetor de visão** (`clip`, BF16): 922 MB no Qwen3.5-9B → 5,6 GB de pesos + 0,92 = ~6,5 GB antes de KV e grafo. Medição de terceiros: ~1,38 GiB a mais de VRAM que o GGUF só-texto.

## Fix / contorno
- Se não usa visão, prefira tag menor ou **GGUF só-texto** via `FROM hf.co/<org>/<repo>:Q4_K_M` (sem `mmproj`).
- Import `hf.co` **não herda** template/tools/thinking/sampling da tag oficial: declare `RENDERER`, `PARSER` e `PARAMETER temperature/top_p/top_k` no Modelfile. Se a versão do Ollama não aceitar `RENDERER`/`PARSER`, o `create` falha; sem eles tools e thinking provavelmente não funcionam.
- Sempre conferir `ollama show` (sem `projector`) e `ollama ps` (`100% GPU`).
- Liberar VRAM de outros apps ajuda (`nvidia-smi`; modo híbrido/Optimus para a tela usar a iGPU).

Não verificado: se o import só-texto realmente mantém tools no Ollama 0.40.

## 🔗 Conexões
- [[Orçamento de VRAM para LLM Local - Pesos, Grafo e KV Cache]]
- [[ollama-8gb-configs|Projeto ollama-8gb-configs]]
