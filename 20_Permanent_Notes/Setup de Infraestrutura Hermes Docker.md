---
title: Setup de Infraestrutura Hermes Docker
type: decision
project: hermes_docker
tags: [docker, ubuntu, infrastructure]
created: 2026-05-21
provenance: 1.0
---

# Setup de Infraestrutura Hermes Docker

Detalhes da configuração do ambiente isolado para o agente.

## Configuração do Container
- **Base**: Ubuntu 22.04.
- **Ferramentas**: `curl`, `git`, `build-essential`, `python3`, `nodejs` (v20+ para suporte a MCP).
- **IA Orchestration**: Inclusão do `google-gemini-cli` instalado globalmente via npm.
- **Socket Docker**: Mapeamento do `/var/run/docker.sock` para permitir "DooD".

## Padrão Multi-Instância e Persistência
A arquitetura foi evoluída para suportar múltiplas instâncias isoladas por projeto:
- **Project Names**: Uso de `COMPOSE_PROJECT_NAME` para isolamento de stacks.
- **Variáveis Dinâmicas**: `HERMES_CONTAINER_NAME`, `WORKSPACE_PATH` e `OAUTH_PORT` permitem subir containers paralelos sem colisão.
- **Persistência Global**: Volume `gemini_data` mapeia `/root/.gemini`, compartilhando tokens de autenticação entre instâncias, mas isolando os arquivos de trabalho.

## Fluxo de Inicialização (`entrypoint.sh`)
O container utiliza um script de entrypoint para garantir que o backend de inferência (Ollama) esteja pronto antes de liberar o terminal para o usuário:
```bash
until curl -s "$OLLAMA_HOST/api/tags" > /dev/null; do
  echo "Waiting for Ollama to be ready..."
  sleep 2
done
```

## Links
- [[hermes_docker]]
- [[Docker-out-of-Docker (DooD)]]

## Fontes
- Arquivos: `Dockerfile`, `entrypoint.sh`
- Documentação: `docs/docker-setup.md`
