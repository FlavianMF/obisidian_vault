---
title: Docker-out-of-Docker (DooD)
type: decision
project: hermes_docker
tags: [docker, security, performance]
created: 2026-05-21
provenance: 1.0
---

# Docker-out-of-Docker (DooD)

Decisão arquitetural de utilizar o motor de Docker do host dentro de um container, em vez de rodar um daemon Docker completo dentro do container (DinD).

## Racional
- **Performance**: Menor overhead comparado ao Docker-in-Docker (DinD).
- **Compartilhamento de Imagens**: O container do agente compartilha o cache de imagens com o host, evitando downloads duplicados.
- **Simplicidade**: Implementado via montagem do socket: `-v /var/run/docker.sock:/var/run/docker.sock`.

## Riscos (Traps)
- **Segurança**: Dar acesso ao `docker.sock` permite que o container do agente controle totalmente o host Docker, o que pode levar a escalada de privilégios. Requer ambientes controlados ou uso de proxies de socket.

## Links
- [[Ambiente de Desenvolvimento de Agentes em Containers]]

## Fontes
- Projeto: [[hermes_docker]]
- Path: `/home/flv/projetos_ai/hermes_docker`
- Documentação: `docs/docker-in-docker.md`
