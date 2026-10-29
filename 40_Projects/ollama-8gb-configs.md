---
title: Projeto ollama-8gb-configs
type: project
tags: [project, ollama, llm, vram, wsl2, capella, opencode]
created: 2026-10-15
provenance: ollama-8gb-configs
status: active
verified: 2026-10-15 via leitura completa do repo (1 commit: ba5eff1)
path: /mnt/c/Users/User/Documents/ollama-8gb-configs
---

# Projeto ollama-8gb-configs

Repo de **docs + Modelfiles** (sem código de aplicação) para rodar LLMs locais no Ollama numa **RTX 5050 Laptop 8 GB** (~6,9 GiB livres; i7-13650HX; 32 GB DDR5-4800). Entra como submodule `docs/ollama` do plugin Capella (`capella_llm_window`). Ollama nativo no Windows, cliente no WSL2. Idioma dos docs: pt-BR.

## Estrutura
- `ollama-windows-wsl2.md`: guia de setup, tuning de hardware, estudos de caso (contexto 262144; Qwen3.8 27B).
- `modelfiles/`: `*-capella.Modelfile` por modelo (qwen3.5-4b, qwen3.5-9b só-texto, qwen3-8b, granite4-tiny, gemma4-e2b, deepseek-r1, qwen3.8 27B) + `create-all.ps1` (pull se faltar, `ollama create`, `-Filter`) + README com comparação ponderada.
- `model-research-8gb-vram.md`: ranking de modelos que cabem 100% GPU.
- `shared-memory-study.md`: sysmem fallback vs CPU.
- `docs/`: `opencode-modelo-local.md`, `qwen3-4b-local-8gb.md` (não commitados ainda).

## Decisões
- Padrão: `qwen3.5-4b-capella` (64K); rápido: `granite4-tiny`; qualidade: `qwen3.5-9b` experimental; 27B só em lote noturno.
- `num_ctx` por Modelfile, global baixo (8192).
- Pesos de comparação: velocidade 35%, tool calling 30%, folga de contexto 15%, thinking 10%, risco 10%.

## Estado (verified 2026-10-15 via git status)
- Working tree: 13 arquivos "modificados" cujo `git diff -w --ignore-cr-at-eol` é vazio, ou seja, **só mudança de fim de linha** (CRLF do checkout no Windows/`/mnt/c`); `docs/` não rastreado.
- **Nenhum número foi medido**: tabelas de eval rate / PROCESSOR / teste A-B estão vazias. Pendente: medir, validar `RENDERER`/`PARSER` do import hf.co, confirmar tool calling dos Qwen3.5 (issues Ollama #14493, #14745).
- Dúvidas abertas: largura de banda real da GPU (224 vs 384 GB/s), link PCIe, contexto máx. do Granite (1M vs 128K).

## Estado (2026-10-29, via artifacts da epic dotfiles)
- Os agentes do Traycer deixaram de usar o Ollama do Windows como backend. Decisão de 2026-10-28: `llama.cpp` direto no WSL2, porque só o `llama-server` faz offload de experts. O Ollama segue para os Modelfiles deste repo.
- A afirmação "nenhum número foi medido" acima vale só para as tabelas do repo; existem números medidos em outro modelo (`qwen3:8b`), ver [[Orçamento de VRAM para LLM Local - Pesos, Grafo e KV Cache]].

## Notas extraídas
- [[Orçamento de VRAM para LLM Local - Pesos, Grafo e KV Cache]]
- [[Tag Multimodal do Ollama Carrega Projetor de Visão e Estoura a VRAM]]
- [[Memória Compartilhada da GPU - CPU Vence no Decode]]
- [[Ollama no Windows Para Cliente no WSL2 - Bind, Firewall e Contexto Global]]
- [[opencode com Modelo Local Único Residente em GPU de 8 GB]]
- Llama.cpp no WSL2: [[llama.cpp para Blackwell no WSL2 - Toolkit do Repo wsl-ubuntu e 120a-real]], [[llama-server - -ngl 99 e --fit Conflitam com --n-cpu-moe e o Health Dá 503 na Carga]], [[Local Primeiro no Traycer - Roteamento de Agentes para llama.cpp com Escalonamento]], [[Plano de Energia Alto Desempenho do Windows Crava a GPU do Notebook em 35 W]]
- Relacionadas: [[Ollama Ignora Tamanho de Contexto Enviado por Request]], [[Detecção Ao Vivo de Janela de Contexto do Ollama via api-ps e api-show]], [[opencode]]
