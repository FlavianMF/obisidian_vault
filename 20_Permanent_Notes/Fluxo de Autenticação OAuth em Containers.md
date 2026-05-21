---
title: Fluxo de Autenticação OAuth em Containers
type: pattern
project: hermes_docker
tags: [oauth, security, docker, networking]
created: 2026-05-21
provenance: 1.0
---

# Fluxo de Autenticação OAuth em Containers

Padrão para lidar com fluxos de autenticação que requerem redirecionamento via navegador (callback) em ambientes CLI rodando dentro de containers.

## Problema
Agentes como o Gemini CLI ou Hermes Agent frequentemente usam Google OAuth, que abre um navegador e redireciona para um `localhost:port`. Dentro de um container ou servidor remoto, esse redirecionamento falha.

## Solução
1. **Exposição de Portas**: Expor a porta de callback (geralmente `8080`) no `docker-compose.yml`.
2. **Tunneling (Se remoto)**: Usar SSH Tunneling para mapear a porta do servidor para o host local:
   `ssh -L 8080:localhost:8080 user@remote-ip`
3. **Redirect URI**: Configurar o provider para aceitar `http://localhost:8080`.

## Links
- [[hermes_docker]]

## Fontes
- Documentação: `docs/oauth-setup.md`
