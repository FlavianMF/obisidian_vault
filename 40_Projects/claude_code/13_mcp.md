---
title: MCP no harness do Claude Code
type: project
tags: [claude-code, mcp, protocol, oauth, gateway]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# MCP no harness

[← Índice](00_indice.md)

O Model Context Protocol aparece em três lugares distintos do repositório, e a leitura
combinada diz mais do que cada um separado.

## 1. `$.mcp.call` — a superfície de plugin

```ts
mcp: {
  call: (server: string, tool: string, args?: Record<string, unknown>) => Promise<McpToolResult>
}
```
`claude-code.d.ts:2091`.

> Chama `tool` num dos servidores MCP conectados do engine **com a conexão e as credenciais
> do próprio engine**. Um servidor `cached` é discado no primeiro uso. Resolve com o
> resultado da ferramenta como o MCP devolve: blocos `content` e `isError`.
> **Sem prompt de permissão: a chamada do plugin, vista pelos hooks acima dele, é a
> concessão.**

A frase em negrito é a decisão de design que vale registrar. Não existe diálogo de permissão
para um plugin chamando MCP — porque o plugin já está *dentro* da cadeia, e quem tinha que
autorizar são os hooks acima dele. A autorização é estrutural, não interativa.

Detalhe prático: o nome do servidor é aceito nas duas grafias — como o `/mcp` lista
(`claude.ai Gmail`) e como o nome de ferramenta o escreve (`claude_ai_Gmail`).

O evento é `mcp.call` com `{ server, tool, args }` (`claude-code.d.ts:4511`) — logo,
`on('mcp.call', ...)` intercepta toda chamada MCP de todo plugin.

## 2. Ferramentas MCP no namespace do modelo

Para o modelo, uma ferramenta MCP é `mcp__<server>__<tool>`, e uma ferramenta registrada por
plugin é `mcp__<plugin>__<name>` ([05](05_sistema_tools.md)). **O mesmo namespace.** Do ponto
de vista do modelo, plugin e servidor MCP são indistinguíveis; a diferença está em quem
executa.

Isso também significa que `tool.check` e `tool.call` cobrem MCP sem nada especial:
`on('tool.call', { tool: 'mcp__github__create_issue' }, ...)` é um hook válido.

O `sec-default` se apoia nisso para a allowlist de MCP da organização: ele recusa
`tool.register` de um chamador do tier `user` enquanto os managed settings tiverem
`allowedMcpServers`, e reconcilia `tool.list` para que as ferramentas dos servidores
gerenciados venham da listagem da organização ([11](11_mod_sec_default.md)).

## 3. Configuração e operação (via CHANGELOG)

O repo não documenta a configuração de MCP — isso está nos docs oficiais. Mas o `CHANGELOG`
de 718 KB é um retrato operacional bem detalhado. Os eixos que aparecem com mais frequência:

### Fontes de configuração
`.mcp.json`, settings, plugins, arquivos de agente, `--mcp-config`, `--strict-mcp-config`,
e `managed-mcp.json` para enterprise. Uma entrada importante:

> Corrigido um `managed-mcp.json` de enterprise que não pode ser lido ou parseado sendo
> ignorado: ele agora **mantém controle exclusivo de MCP** (servidores de usuário, projeto e
> plugin não carregam) e avisa no startup.

Fail closed de novo, coerente com o `sec-default`.

### Transportes e negociação de protocolo
- `stdio`, `http` (Streamable HTTP), e o legado HTTP+SSE.
- Cliente **v2** e negociação MCP `2026-07-28` viraram default até nos installs
  Bedrock/Vertex/Foundry e nos com telemetria desligada; opt-out por
  `MCP_SDK_GENERATION=v1` ou `MCP_PROTOCOL_NEGOTIATION=legacy`.
- `"type": "sdk"` em `.mcp.json`/settings/plugins/agentes é **pulado com aviso**: só uma
  aplicação host do SDK pode registrar servidores in-process.

### Timeouts e startup
`MCP_TIMEOUT`, `timeout` por servidor, e `CLAUDE_CODE_MCP_STARTUP_WAIT_MS` (`0` = não
esperar) para limitar quanto o primeiro turno não-interativo espera por servidores
conectando. Há várias correções em torno de "o primeiro turno começou sem as ferramentas de
um servidor que ainda conectava" — e a solução recorrente é **tool search** com
`alwaysLoad`/`defer_loading`, que deixa a ferramenta chegar num turno posterior em vez de
segurar o turno.

Isso é relevante para qualquer harness: servidor MCP lento é o caso normal, não a exceção, e
o design tem que tolerar ferramentas aparecendo no meio da sessão.

### OAuth e escopos
DCR, consentimento, redirect URI, porta local de callback, expiração no meio da sessão, e
`403 insufficient_scope`. Uma correção mostra a qualidade de mensagem que o harness busca:

> Corrigido chamadas de ferramenta MCP recusadas com `403 insufficient_scope` sendo
> reportadas como login expirado: o erro agora **nomeia as permissões faltantes** e aponta
> para a reautenticação por `/mcp`.

### Vazamento de segredo em `${VAR}`
Duas entradas distintas corrigem segredos resolvidos de placeholders `${VAR}` aparecendo em
mensagens de erro, em `/mcp`, `/plugin`, `claude mcp list/get` e na descrição da ferramenta
de login. Vale como lembrete de que **expansão de variável em config é um vetor de
vazamento** em qualquer harness que faça isso.

### `list_changed`
Duas entradas em direções opostas: refrescar prompts e recursos mesmo quando o servidor não
declara `listChanged`; e **não** derreter a CPU quando um servidor manda `list_changed` em
loop apertado. Robustez contra servidor mal-comportado é requisito, não extra.

### Servidor, não só cliente
`claude mcp serve` — o Claude Code **é** um servidor MCP também. Uma melhoria registrada:
"uma chamada de ferramenta em curso agora manda atualização de progresso a cada 30 segundos,
para que clientes mostrem que ainda está rodando e timeouts de idle não abortem um comando
longo que não imprime nada".

## O gateway: Claude apps gateway

`examples/gateway/` tem 26 arquivos e é, na prática, um produto à parte: uma referência de
deploy do **Claude apps gateway**, com upstream em Bedrock (AWS) ou Vertex (GCP).

| Arquivo | O que é |
|---|---|
| `setup.sh` | roteiro fim a fim via CLI do provedor |
| `Dockerfile` | imagem do binário `claude gateway` |
| `gateway.yaml.example` | template de config |
| `terraform/` | a arquitetura inteira (apply em duas passadas) |

Componentes na versão AWS: ECS Fargate ou EKS, RDS PostgreSQL, Secrets Manager, auth por IAM
role para o Bedrock, Okta como IdP, ALB interno.

O `gateway.yaml.example` é um documento de segurança disfarçado de config. Dois trechos que
valem citar:

> `public_url` — **Obrigatório.** Fixa o `redirect_uri` do IdP, o documento de discovery OIDC
> e o emissor do token do gateway, para que nenhum deles seja derivado do header `Host`
> controlado pelo cliente (`X-Forwarded-Host`/`-Proto` igualmente nunca são confiados).

> **NOTA:** listar os CIDRs das subnets do ALB confia em todo host dessas subnets como proxy
> — qualquer workload colocado ali que alcance o ALB pode então forjar o IP do cliente via
> `X-Forwarded-For` (logs de auditoria, rate limit por IP, allowlists de IP).

Expansão de segredo: `${ENV_VAR}` lê variável de ambiente, `${file:/path}` lê arquivo
montado. E `setup.sh` **recusa construir a imagem enquanto houver qualquer `REPLACE_ME`** —
porque a config é baked na imagem e uma config pela metade embarcaria.

O gateway não é MCP estritamente; entra aqui porque é o outro lado do mesmo problema — como
uma organização coloca um ponto único de controle entre o harness e os modelos. Aparece
também no `CHANGELOG` com config própria (`store.connect_timeout_seconds`,
`store.postgres_url`, limite de 256 requisições simultâneas por réplica).

## Ver também

- [05](05_sistema_tools.md) — o namespace `mcp__server__tool`
- [11](11_mod_sec_default.md) — `allowedMcpServers` e a reconciliação de `tool.list`
- [17](17_evolucao_changelog.md) — o resto do que o CHANGELOG conta
