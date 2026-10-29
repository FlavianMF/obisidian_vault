---
title: llama-server - -ngl 99 e --fit Conflitam com --n-cpu-moe e o Health Dá 503 na Carga
type: trap
tags: [llama-cpp, llama-server, moe, fit, health-check, shell-script, testing]
created: 2026-10-29
provenance: dotfiles
project: dotfiles
verified: 2026-10-29 via artifact de review (leitura do fonte llama.cpp ac8e169 em 2026-10-28; linhas citadas não relidas hoje)
confidence: low
seen_in: [dotfiles]
---

# llama-server - -ngl 99 e --fit Conflitam com --n-cpu-moe e o Health Dá 503 na Carga

Cinco armadilhas achadas ao revisar um script que sobe o `llama-server` com `gpt-oss-20b` em GPU de 8 GB.

1. **`-ngl 99` + `--fit on` abortam o fit.** Os dois já são o padrão: `-ngl -1` põe todas as camadas na GPU (`src/llama-model.cpp:2446`) e `--fit` vem `on`. Com `--n-cpu-moe`, o fit aborta (`common/fit.cpp:566`) porque `tensor_buft_overrides` já está preenchido. Remova `-ngl`; no ramo com offload de experts passe `-fit off`.
2. **`/health` devolve 503 "Loading model"** depois do bind HTTP e até o fim de `load_model` (`tools/server/server-http.cpp:319`). Antes disso, com `-hf`, o servidor **baixa o modelo antes do bind** (`tools/server/server.cpp:614` vs `:659`): durante o primeiro download de ~12 GB a porta está livre. Um `curl -f` no health lê os dois casos como "fora" e dispara uma segunda instância. Antes de subir, `pgrep -x llama-server`; se houver processo, espere o health.
3. **Sem `--n-cpu-moe`, um MoE de 12 GB tenta caber inteiro em 8 GB:** erro CUDA na carga, ou, com o fallback do driver ligado, lentidão silenciosa (ver [[Memória Compartilhada da GPU - CPU Vence no Decode]]).
4. **Descarga do Ollama ignora a URL configurada** se o script fixa `127.0.0.1:11434`. Use `${OLLAMA_BASE_URL:-...}` sem o sufixo `/v1` e avise quando `/api/ps` não responder, senão o `llama-server` sobe com a VRAM ocupada.
5. **Teste com binário falso não pega flag inválida:** o `llama-server` falso aceitava qualquer flag e as asserções comparavam a string literal do script, então a falha 1 passou. Acrescente um teste de contrato (cada flag do script aparece em `llama-server --help`; pule se o binário não existir) e um que ligue o `jq` real ao ramo de descarga.

Observação: `-hf ggml-org/gpt-oss-20b-GGUF` sem quant cai no primeiro arquivo do repo (`--help`).

## O que NÃO funcionou
- O script original (`-ngl 99`, `--fit on`, health como detector de "fora"): bloqueio no review. Corrigido em commits `642fc49` e `79b4e23` (`bin/llm-serve`).
- Os testes do script passavam com o bug: o fake espelhava o código.
- Não verificado: o contrato por `--help` e o teste do ramo Ollama foram **propostos**; não sei se entraram.

## 🔗 Conexões
- [[MoE em GPU de 8 GB - Offload de Experts com llama.cpp]]
- [[llama.cpp para Blackwell no WSL2 - Toolkit do Repo wsl-ubuntu e 120a-real]]
