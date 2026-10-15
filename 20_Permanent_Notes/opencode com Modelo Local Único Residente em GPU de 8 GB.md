---
title: opencode com Modelo Local Único Residente em GPU de 8 GB
type: pattern
tags: [opencode, ollama, llm, agents, vram, model-swap, harness]
created: 2026-10-15
provenance: ollama-8gb-configs
project: ollama-8gb-configs
verified: 2026-10-15 via leitura de docs/opencode-modelo-local.md (config descrita, não executada nesta sessão)
confidence: low
seen_in: [ollama-8gb-configs]
---

# opencode com Modelo Local Único Residente em GPU de 8 GB

Com 8 GB cabe **um** modelo por vez (`OLLAMA_MAX_LOADED_MODELS=1`); trocar descarrega e recarrega do disco. Logo, nenhum modelo diferente no caminho quente.

- Registrar provider `@ai-sdk/openai-compatible` com `baseURL` `http://<host>:11434/v1` em `~/.config/opencode/opencode.jsonc`; o ID do modelo tem que bater exato com `/v1/models`. Sem hot-reload: reabrir o opencode. Sem API key (dummy `"ollama"` se reclamar). Precisa da capability `tools` para edit/bash.
- **Não fixar `model` global** nem apontar para o modelo grande: `build`/`plan` nativos ficam de fábrica; agentes `build-local`/`plan-local` (4B, 64K) em `~/.config/opencode/agent/`; `small_model` = 4B (título/compaction, 0 swap).
- Escalação explícita por agente primário: `deep` (Qwen3 8B, 12K, 1 swap) e `night` (Qwen3.8 27B split CPU/GPU, ~3-6 tok/s, só lote).
- Prompts de agente para modelo pequeno/contexto curto: passos pequenos, `grep`/`glob` + Read com `offset`/`limit`, edição alvo, `steps` limitado, `plan` com `edit: deny`, e "pare e recomende `deep`/`night`" quando faltar raciocínio.
- Contexto: endpoint `/v1` ignora `num_ctx`; vale o Modelfile ([[Ollama Ignora Tamanho de Contexto Enviado por Request]]).
- Recomendação de modelos (comparação ponderada, não medida): `qwen3.5-4b` padrão (4,35), `granite4:7b-a1b-h` mais rápido (4,00, sem thinking), `qwen3.5-9b` só-texto experimental (3,85); evitar `gemma4:e2b` (relato de renderer descartando parâmetros de tool chamados `type`/`description`/`properties`/`required`/`nullable`) e `deepseek-r1:8b`.

## 🔗 Conexões
- [[opencode]]
- [[Orçamento de VRAM para LLM Local - Pesos, Grafo e KV Cache]]
- [[ollama-8gb-configs|Projeto ollama-8gb-configs]]
