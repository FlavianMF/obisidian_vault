---
title: Permissões e segurança — quatro camadas
type: project
tags: [claude-code, security, permissions, sandbox, mdm]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Permissões e segurança

[← Índice](00_indice.md)

A segurança do harness está espalhada por **quatro camadas independentes**, e a propriedade
interessante é que cada uma falha sozinha sem derrubar as outras.

| Camada | Onde vive | Quem controla |
|---|---|---|
| 1. Regras declarativas | `settings.json` — `permissions.allow/ask/deny` | pessoa, projeto, organização |
| 2. Veredito em código | evento `tool.check` | plugins, por tier |
| 3. Isolamento do ambiente | `sandbox` nos settings, ambiente do plugin | organização, binário |
| 4. Assento na cadeia | os cinco tiers + `sec-default` | o binário e a organização |

## Camada 1 — regras declarativas

`permissions.allow` / `ask` / `deny`, com a sintaxe de regra que aparece no veredito:
`Bash(git push:*)` (`ToolCheckResult.rule`, [05](05_sistema_tools.md)).

`examples/settings/` publica três perfis prontos, e a tabela do README deles é a melhor
documentação compacta da superfície:

| Controle | `settings-lax.json` | `settings-strict.json` | `settings-bash-sandbox.json` |
|---|:---:|:---:|:---:|
| Desabilita `--dangerously-skip-permissions` | ✅ | ✅ | |
| Bloqueia marketplaces de plugin | ✅ | ✅ | |
| Bloqueia `allow`/`ask`/`deny` de usuário e projeto | | ✅ | ✅ |
| Bloqueia hooks de usuário e projeto | | ✅ | |
| Nega WebFetch e WebSearch | | ✅ | |
| Bash exige aprovação | | ✅ | |
| Bash só roda dentro do sandbox | | | ✅ |

As chaves que implementam isso (`settings-strict.json`):

```json
{
  "permissions": { "disableBypassPermissionsMode": "disable", "ask": ["Bash"], "deny": ["WebSearch", "WebFetch"] },
  "allowManagedPermissionRulesOnly": true,
  "allowManagedHooksOnly": true,
  "strictKnownMarketplaces": []
}
```

`allowManagedPermissionRulesOnly`, `allowManagedHooksOnly` e `strictKnownMarketplaces` são
**meta-regras**: elas não dizem o que é permitido, dizem *quem pode dizer*. E o README avisa
que "certas propriedades só têm efeito se especificadas em settings de enterprise".

## Camada 2 — veredito em código (`tool.check`)

Detalhada em [05](05_sistema_tools.md). O resumo:
`allow | ask | deny`, com `reason` e `rule`; a última palavra subindo a cadeia vence;
`$.tool.check` consulta sem executar; `next.origin` distingue "o modelo quer" de "o plugin X
quer".

O caminho clássico equivalente é o hook `PreToolUse`, e o repo publica um exemplo mínimo
(`examples/hooks/bash_command_validator_example.py`, 83 linhas):

```python
_VALIDATION_RULES = [
    (r"^grep\b(?!.*\|)", "Use 'rg' (ripgrep) instead of 'grep' ..."),
    (r"^find\s+\S+\s+-name\b", "Use 'rg --files | rg pattern' ... instead of 'find -name'"),
]
```

Lê JSON no stdin, valida, escreve no stdout. É o "hello world" de política de ferramenta.

## Camada 3 — sandbox

O bloco `sandbox` (`settings-bash-sandbox.json`) é a superfície mais detalhada:

```json
"sandbox": {
  "enabled": true,
  "autoAllowBashIfSandboxed": false,
  "allowUnsandboxedCommands": false,
  "excludedCommands": [],
  "network": {
    "allowUnixSockets": [], "allowAllUnixSockets": false, "allowLocalBinding": false,
    "allowedDomains": [], "httpProxyPort": null, "socksProxyPort": null
  },
  "enableWeakerNestedSandbox": false
}
```

Rede é tratada como eixo separado: domínios permitidos, sockets Unix, binding local, portas
de proxy HTTP/SOCKS. `enableWeakerNestedSandbox` é o reconhecimento explícito de que sandbox
aninhado (container dentro de container) degrada.

**O limite está documentado, e é importante**:

> A propriedade `sandbox` **só se aplica à ferramenta Bash**; ela não se aplica a outras
> ferramentas (como Read, Write, WebSearch, WebFetch, MCPs), a hooks, nem a comandos internos.
>
> — `examples/settings/README.md`

Ou seja: sandbox não é uma jaula do processo inteiro; é uma jaula de uma ferramenta. Quem
depender dele para contenção precisa somar com `deny` nas outras ferramentas — que é
exatamente o que o `settings-strict.json` faz.

Separadamente, o **ambiente dos plugins** é uma contenção de natureza diferente: sem DOM, sem
Node, sem fs/rede/processo direto, acesso ao mundo só via `$` ([02](02_modelo_engine_hooks.md)).
Ali a contenção é total e o mecanismo é a própria API.

## Camada 4 — assento

Ver [11](11_mod_sec_default.md). O resumo do argumento: como a API de hooks dá a todo plugin
uma palavra em todo evento, controles organizacionais que antes eram inalcançáveis
(hooks clássicos, CLAUDE.md gerenciado, settings, allowlist de MCP) passariam a ser
alcançáveis. O `sec-default`, assentado no tier mais externo, restaura o invariante com três
movimentos e nenhuma política própria.

A propriedade que amarra tudo: **`next.to` é recusado fora de um tier gerenciado**. A
autoridade é o assento, não o código.

## Distribuição: MDM

`examples/mdm/` mostra como uma organização entrega a camada 1 na frota:

| Arquivo | Para |
|---|---|
| `managed-settings.json` | qualquer plataforma, no diretório de config do sistema |
| `macos/com.anthropic.claudecode.plist` | payload Custom Settings do Jamf/Iru (domínio `com.anthropic.claudecode`) |
| `macos/com.anthropic.claudecode.mobileconfig` | perfil de configuração completo |
| `windows/Set-ClaudeCodePolicy.ps1` | Intune Platform scripts; escreve em `C:\Program Files\ClaudeCode\` |
| `windows/ClaudeCode.admx` + `.adml` | Group Policy / Intune ADMX; escreve `HKLM\SOFTWARE\Policies\ClaudeCode\Settings` (REG_SZ, JSON numa linha) |

Todos os cinco codificam o **mesmo** exemplo mínimo,
`{"permissions": {"disableBypassPermissionsMode": "disable"}}` — deliberadamente, para que a
diferença entre eles seja só o mecanismo de entrega.

Dica operacional que vale registrar: confirmar com `/status`, que lista a fonte sob
**Setting sources** (`Enterprise managed settings (plist)` no macOS,
`Enterprise managed settings (HKLM)` no Windows). "Settings entregues assim ficam no topo da
ordem de precedência e não podem ser sobrepostos por usuários."

## Um exemplo completo de política como plugin

`plugins/security-guidance` é o caso mais rico do repo e mistura as camadas:

- **Hooks clássicos** em `PreToolUse`/`PostToolUse`/`UserPromptSubmit`/`Stop`, em Python.
- **9 padrões de regex** com lembretes escritos para o modelo (`hooks/patterns.py`):
  injeção de comando, XSS, `eval`, HTML perigoso, desserialização de pickle, `yaml.load`,
  `torch.load` com `weights_only=False`, `os.system`, e edição de workflow do GitHub Actions.
- **Revisão por LLM** de verdade: `hooks/llm.py` + `hooks/review_api.py` + `ensure_agent_sdk.py`
  — o plugin instala o Agent SDK no `SessionStart` (timeout 180 s) e depois roda revisão de
  segurança sobre o diff.
- **`asyncRewake`** nos hooks de `Bash(git commit:*)` e `Bash(git push:*)`: a revisão roda em
  background e reacorda a sessão com os achados ([08](08_plugins_e_mods.md)).

O `patterns.py` declara no cabeçalho a disciplina que usa: *"Pure data + one pure helper. No
env-var reads, no I/O, no debug_log — kept side-effect-free so it can be imported in
isolation."* A parte que decide é testável sozinha; a parte que age está em outro arquivo.

## Reporte de vulnerabilidade

`SECURITY.md`: programa gerido no HackerOne, com bug bounty. Não há processo de disclosure
específico do repositório além disso.

## Ver também

- [05](05_sistema_tools.md) — `tool.check` em detalhe
- [11](11_mod_sec_default.md) — a camada de assento
- [15](15_config_settings.md) — a hierarquia de settings inteira
