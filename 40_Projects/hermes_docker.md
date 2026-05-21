---
title: Projeto hermes_docker
type: project
status: active
tags: [project, agentic-ai, docker, infrastructure]
created: 2026-05-21
path: /home/flv/projetos_ai/hermes_docker
---

# Projeto hermes_docker

Infraestrutura em containers para execução isolada e segura do **Hermes Agent** em ambiente de desenvolvimento.

## 📌 Visão Geral
Este projeto resolve a necessidade de um ambiente de desenvolvimento "sandbox" onde um agente autônomo possa executar comandos, instalar ferramentas e realizar pesquisas sem afetar diretamente o sistema host, utilizando **Docker-out-of-Docker (DooD)** para permitir que o agente gerencie seus próprios containers de ferramentas.

## 🧠 Conceitos e Padrões Extraídos
- [[Ambiente de Desenvolvimento de Agentes em Containers]] (Padronização)
- [[Docker-out-of-Docker (DooD)]] (Decisão de Performance)
- [[Otimização de Recursos para LLMs em CPU]] (Mitigação de Hardware)

## 🛠️ Documentação Técnica
- [[Setup de Infraestrutura Hermes Docker]]
- [[Integração NVIDIA NIM]]
- [[Fluxo de Autenticação OAuth em Containers]]
- [[Pesquisa Hermes Agent]]

## 📂 Estrutura do Projeto
- `Dockerfile`: Configuração da imagem base (Ubuntu 22.04).
- `docker-compose.yml`: Orquestração Agent + Ollama.
- `entrypoint.sh`: Script de sincronização com o backend de inferência.

## Links
- [[Engenharia de Sistemas]] (MOC)
- [[MBSE com Agentic AI]]
