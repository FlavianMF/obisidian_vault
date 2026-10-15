---
title: Ollama no Windows Para Cliente no WSL2 - Bind, Firewall e Contexto Global
type: trap
tags: [ollama, wsl2, windows, firewall, networking, num_ctx, env-vars]
created: 2026-10-15
provenance: ollama-8gb-configs
project: ollama-8gb-configs
verified: 2026-10-15 via leitura de ollama-windows-wsl2.md (estudo de caso real de 2026-10-08, Ollama 0.40.1)
confidence: medium
seen_in: [ollama-8gb-configs]
---

# Ollama no Windows Para Cliente no WSL2 - Bind, Firewall e Contexto Global

Setup: Ollama **nativo no Windows** (acesso direto ao driver, sem teto de RAM da VM), cliente (Capella/opencode) no WSL2 em NAT.

## Armadilhas
1. **`localhost` no WSL é o WSL.** Ollama escuta só em `127.0.0.1` → `Connection refused`. Fix: `setx OLLAMA_HOST 0.0.0.0:11434` + *Quit Ollama* na bandeja e reabrir (`setx` só vale para processos novos). Conferir `netstat -ano | findstr 11434` = `0.0.0.0`.
2. **Firewall:** regra Allow só para `172.16.0.0/12` (faixa do WSL); nunca sem `-RemoteAddress` (Ollama não tem auth). Se o pop-up do firewall foi cancelado, o Windows cria regra **Block** do `ollama.exe`, que vence a Allow (timeout no curl).
3. **IP do gateway muda** após reboot/`wsl --shutdown`: `ip route show default | awk '{print $3}'`. Alternativa: `networkingMode=mirrored` no `.wslconfig` (Win11 22H2+), `localhost` funciona, sem regra de firewall.
4. **`OLLAMA_CONTEXT_LENGTH=262144` global forçou offload** (caso real): KV de 17-32 GiB empurrou quase tudo para a CPU. Padrão automático do Ollama seria 4096. Corrigir com contexto seguro global (8192) + `num_ctx` por Modelfile. Diagnóstico por variável: FLASH_ATTENTION `false` (anula KV q8_0), KV_CACHE_TYPE vazio (f16), MAX_LOADED_MODELS 0, KEEP_ALIVE 5m, VULKAN true (descoberta de GPU ~16 s, causa não confirmada) → `OLLAMA_VULKAN=0`.
5. **Log de startup só prova config.** Para provar 100% GPU: `ollama ps` (PROCESSOR) e `offloaded N/M layers to GPU` após carregar.
6. Gerenciador de Tarefas: o gráfico "3D" mostra ~0% mesmo com CUDA ativo; trocar para "Cuda"/"Compute". Notebook híbrido: `ollama.exe` em "Alto desempenho" nas configurações gráficas.

## 🔗 Conexões
- [[Ollama Ignora Tamanho de Contexto Enviado por Request]]
- [[Orçamento de VRAM para LLM Local - Pesos, Grafo e KV Cache]]
- [[Projeto ollama-8gb-configs]]
