---
title: Otimização de Recursos para LLMs em CPU
type: trap
project: hermes_docker
tags: [ollama, cpu, performance, llm]
created: 2026-05-21
provenance: 1.0
---

# Otimização de Recursos para LLMs em CPU

Identificação de gargalos e estratégias para rodar modelos de linguagem em ambientes sem GPU (NVIDIA).

## Trap (Armadilha)
Tentar rodar modelos grandes (ex: 8B ou 70B) apenas em CPU resulta em latência extremamente alta (tokens por segundo muito baixo), tornando o uso de agentes interativos frustrante.

## Estratégias de Mitigação
1. **Modelos Menores**: Utilizar variantes de 3B (ex: `hermes3:3b` ou `phi3`) que são significativamente mais responsivas em CPU.
2. **Threading**: Garantir que o Docker tenha acesso a todos os núcleos da CPU e que o Ollama esteja detectando corretamente.
3. **Swap**: Ativar memória Swap se a RAM física for insuficiente para evitar crashes (OOM - Out of Memory).
4. **OLLAMA_NOPRELOAD**: Usar a variável de ambiente `OLLAMA_NOPRELOAD=1` para liberar memória quando o modelo não estiver em uso.

## Links
- [[Ambiente de Desenvolvimento de Agentes em Containers]]

## Fontes
- Projeto: `hermes_docker`
- Documentação: `docs/resource-optimization.md`
