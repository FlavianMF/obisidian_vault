---
title: Servidor MCP do Home Assistant para Agentes de IA
type: pattern
tags: [home-assistant, mcp, ai-agents, automation, devops, tailscale]
created: 2026-10-31
provenance: dotfiles
seen_in: [dotfiles]
verified: 2026-10-31 via testes TDD em tests/ha_mcp_test.sh (24 assercoes) e suite completa make test no dotfiles
confidence: medium
scope: global
---

# Servidor MCP do Home Assistant para Agentes de IA

**A integração entre Home Assistant e CLIs de agentes de IA (Claude Code, Gemini CLI, OpenCode, Cursor) através do Model Context Protocol (MCP) viabiliza o controle operacional da casa inteligente, a depuração de falhas de automação e a gestão declarativa de entidades e dashboards em linguagem natural.**

## Contexto e Problema

Agentes de desenvolvimento baseados em LLM que executam em terminais locais precisam interagir com ecossistemas de automação residencial (como instâncias remotas de Home Assistant conectadas a brokers MQTT e clientes Windows via HASS.Agent). Tradicionalmente, isso exigia scripts ad-hoc usando a REST API com `curl`, sem introspecção de schema, autodescoberta de ferramentas nem rastreabilidade de erros de automação.

Com o advento do Model Context Protocol (MCP), a API do Home Assistant passa a ser exposta como um conjunto estruturado de ferramentas (tools) e recursos (resources) chamáveis pelos agentes.

## Arquitetura e Soluções Disponíveis

Existem duas abordagens principais para integrar o Home Assistant via MCP:

1. **`ha-mcp` (homeassistant-ai/ha-mcp - Recomendado para desenvolvimento e CLIs):**
   - Servidor Python/FastMCP mantido pela comunidade com mais de 80 ferramentas.
   - Além de leitura de sensores e acionamento de serviços, permite:
     - Criar, inspecionar e editar automações e scripts YAML.
     - Analisar *traces* de execução para diagnosticar por que uma automação não disparou.
     - Ajustar cards e layouts no Lovelace.
     - Consultar logs do sistema.
   - Pode ser executado sob demanda via `uvx ha-mcp` (stdio) ou em container Docker/HACS via HTTP Streamable/SSE.

2. **Integração Oficial Home Assistant Core (`mcp_server`):**
   - Nativa a partir das versões recentes do Home Assistant Core.
   - Disponível via `/api/mcp` utilizando transporte HTTP/SSE.
   - Foco em controle seguro e conversacional via motor de voz (*Assist*), restrito às entidades explicitamente expostas na interface.

## Configuração para CLIs de Agentes

### Claude Code CLI
Execução local transparente via `uvx`:
```bash
claude mcp add home-assistant \
  --scope user \
  --env HOMEASSISTANT_URL="http://<IP_OU_HOST_TAILSCALE>:8123" \
  --env HOMEASSISTANT_TOKEN="<LONG_LIVED_ACCESS_TOKEN>" \
  -- uvx ha-mcp@latest
```

### Gemini CLI / OpenCode / Cursor
Em `settings.json` ou arquivo de configuração MCP:
```json
{
  "mcpServers": {
    "homeassistant": {
      "command": "uvx",
      "args": [
        "ha-mcp",
        "--url", "http://<IP_OU_HOST_TAILSCALE>:8123",
        "--token", "<LONG_LIVED_ACCESS_TOKEN>"
      ]
    }
  }
}
```

## Topologia de Rede e Segurança (Tailscale Mesh)

Em ambientes com Home Assistant conteinerizado na VPS e agentes de desenvolvimento no host local (WSL2/Windows):
- O tráfego MCP e API trafega diretamente pela malha criptografada Tailscale (ex: `100.x.y.z:8123`).
- Nenhuma porta pública do Home Assistant precisa ser exposta para a internet.
- A autenticação é estritamente baseada em *Long-Lived Access Tokens* gerenciados pelo perfil do Home Assistant.

## O que NÃO funcionou

- **Usar a integração nativa Core (`mcp_server`) para engenharia de automações:** A integração oficial restringe as ações às entidades expostas para o Assist de voz. Ela não possui ferramentas para editar YAML, debugar traces de execução de automações nem inspecionar logs de erro do sistema, tornando-a insuficiente para um agente que programa ou depura o sistema. O `ha-mcp` foi necessário para esse propósito.
- **Instalar o pacote MCP via `pip install` global:** Gera poluição no ambiente Python do sistema e risco de conflitos de dependências com ferramentas do sistema operacional. O uso de `uvx ha-mcp` (via uv) resolve a execução isolando automaticamente as dependências em cache temporário.
- **Exposição de portas HTTP na VPS sem túnel VPN:** Tentar conectar agentes remotos à porta `8123` aberta diretamente gerava tráfego não criptografado e risco severo de segurança contra o painel de controle físico. O túnel ponto a ponto Tailscale eliminou a necessidade de portas públicas ou proxies reversos complexos na fase inicial.
