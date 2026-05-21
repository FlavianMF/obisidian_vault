---
title: Integração NVIDIA NIM
type: concept
project: hermes_docker
tags: [nvidia, nim, ai-inference, api]
created: 2026-05-21
provenance: 1.0
---

# Integração NVIDIA NIM

Uso do NVIDIA NIM (Inference Microservices) como backend de inferência para agentes autônomos.

## Descrição
NVIDIA NIM fornece uma API compatível com o padrão OpenAI para modelos de linguagem e visão, permitindo que ferramentas desenhadas para OpenAI funcionem transparentemente com a infraestrutura NVIDIA.

## Configuração no Hermes Agent
- **Provider**: Selecionar `OpenAI compatible`.
- **Base URL**: `https://integrate.api.nvidia.com/v1`.
- **API Key**: Gerada no dashboard da NVIDIA.

## Links
- [[hermes_docker]]
- [[Otimização de Recursos para LLMs em CPU]] (Alternativa local)

## Fontes
- Documentação: `docs/nvidia-nim-research.md`
