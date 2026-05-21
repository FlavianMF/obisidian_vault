---
title: Ambiente de Desenvolvimento de Agentes em Containers
type: pattern
project: hermes_docker
tags: [docker, agentic-ai, isolation, dev-environment]
created: 2026-05-21
provenance: 1.0
---

# Ambiente de Desenvolvimento de Agentes em Containers

Padronização de infraestrutura isolada para execução de agentes autônomos (como o Hermes Agent) utilizando Docker para garantir reprodutibilidade e segurança.

## Descrição
O padrão consiste em um setup multi-container onde o agente reside em um container isolado e se comunica com backends de inferência (locais ou nuvem) e ferramentas do host.

## Componentes Chave
1. **Container do Agente**: Baseado em Ubuntu com ferramentas CLI (Hermes, Node.js, Python) e Docker CLI.
2. **Incerência Local (Ollama)**: Container dedicado para rodar modelos como `hermes3:8b`.
3. **Persistência**: Volume mount do `./workspace` do host para `/workspace` no container.
4. **Tool Use**: Acesso ao socket do Docker do host (`/var/run/docker.sock`) para criação de sandboxes temporários.

## Links
- [[MBSE com Agentic AI]]
- [[Agentic AI]]
- [[Docker-out-of-Docker (DooD)]]

## Fontes
- Projeto: `hermes_docker`
- Documentação: `docs/docker-setup.md`, `docker-compose.yml`
