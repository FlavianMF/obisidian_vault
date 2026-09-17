---
title: O runtime observado em disco
type: project
tags: [claude-code, persistence, jsonl, session, observability]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# O runtime, observado em disco

[← Índice](00_indice.md)

> **Escopo e método.** Este capítulo é a única parte da pesquisa que não vem do repositório
> nem dos docs. Ele observa **o que a instalação local escreve em disco** — nomes de
> diretório, formatos de arquivo, chaves de JSON — na máquina do usuário, versão `2.1.274`.
>
> O que **não** foi feito, por decisão explícita: desmontar, descompilar ou extrair strings
> do binário (produto proprietário); ler `~/.claude/.credentials.json`; transcrever conteúdo
> de conversa. Onde um arquivo contém credencial, só o **nome da chave** é registrado, nunca
> o valor.

## O binário

```
~/.local/share/claude/versions/
  2.1.266  216 MB
  2.1.267  217 MB
  2.1.268  219 MB
  2.1.274  231 MB
```

`file` diz: `ELF 64-bit LSB executable, x86-64, dynamically linked, not stripped`.
Executável único, sem `node_modules`, tamanho compatível com um bundle Bun com runtime
embutido. `~/.local/bin/claude` aponta para a versão corrente; versões antigas ficam para
rollback (e o `CHANGELOG` menciona "auto-update relaunch", que explica por que mais de uma
fica em disco).

Isso confirma, do lado de fora, o que o README diz: `npm install -g` está **deprecado** em
favor de `curl … | bash`, Homebrew cask, WinGet. A distribuição saiu do npm.

## O mapa de `~/.claude`

| Caminho | Tamanho aqui | O que é |
|---|---:|---|
| `projects/` | 234 MB | **Transcrições**, uma pasta por diretório de trabalho |
| `jobs/` | 34 MB | Sessões em background e seu histórico de estado |
| `file-history/` | 12 MB | Versões de arquivos editados, para `/rewind` |
| `plugins/` | 11 MB | Marketplaces, cache, plugins instalados, sincronizados |
| `skills/` | 4,3 MB | Skills |
| `shell-snapshots/` | 3,7 MB | Snapshots do shell do usuário |
| `session-env/` | 976 KB | Uma pasta por sessão |
| `telemetry/` | 948 KB | Eventos que **falharam** ao enviar |
| `cache/` | 724 KB | Inclui `changelog.md` |
| `plans/` | 576 KB | Planos do plan mode, um `.md` por plano |
| `backups/` | 504 KB | `.claude.json.backup.<epoch_ms>` |
| `sessions/` | 364 KB | Um JSON por processo |
| `tasks/` | 120 KB | Uma pasta por sessão com tarefas |
| `daemon/`, `daemon.log`, `daemon.lock`, `daemon.status.json` | — | O daemon |
| `ide/`, `downloads/`, `paste-cache/`, `gh-pr-status-cache.json` | — | Auxiliares |
| `history.jsonl` | — | Histórico de prompts digitados |
| `settings.json` | — | Aqui, um symlink para os dotfiles do usuário |

Observação útil: **`settings.json` funciona como symlink**. Versionar settings em dotfiles e
linkar é um padrão que o harness suporta na prática.

## O formato da transcrição

`projects/<cwd-com-barras-viradas-em-hifens>/<session-uuid>.jsonl`, JSON Lines, um registro
por linha. O diretório de trabalho vira nome de pasta trocando `/` por `-`
(`/home/flv/projetos_ita` vira `-home-flv-projetos-ita`).

Tipos de registro observados numa amostra de 200 linhas de uma sessão real:

| `type` | Papel |
|---|---|
| `assistant` | turno do modelo |
| `user` | turno do usuário |
| `attachment` | anexo/contexto atrelado a um turno |
| `system` | mensagem de sistema |
| `file-history-snapshot` | ponto de restauração de arquivo |
| `ai-title` | título gerado da sessão |
| `agent-name` | nome do agente |
| `mode`, `permission-mode` | mudança de modo |
| `queue-operation` | operação de fila de prompts |
| `atis-latch` | trava interna |

Chaves de topo observadas (união da amostra) — vale a lista inteira porque ela é o esquema
efetivo para quem for minerar transcrições:

```
agentName, aiTitle, apiBlockIndex, atis, attachment, attributionSkill, content, cwd,
durationMs, effort, entrypoint, gitBranch, interruptedMessageId, isMeta, isSidechain,
isSnapshotUpdate, message, messageCount, messageId, mode, operation, origin, parentUuid,
permissionMode, promptId, promptSource, rendered, renderedInHumanTurn, requestId,
sessionId, sessionKind, session_id, snapshot, sourceToolAssistantUUID, sourceToolUseID,
subtype, timestamp, toolDenialKind, toolUseResult, turnCompanion, type, userFeedback,
userType, uuid, version
```

Correspondências diretas com o contrato ([03](03_event_surface.md), [04](04_agent_loop_turn.md)):

- `parentUuid` — a transcrição é uma **árvore**, não uma lista. É o que permite `/rewind`,
  fork e branches de conversa.
- `isSidechain` — marca o que não é o fio principal (subagente, companion).
- `effort` — o mesmo campo reescrevível de `turn.step`.
- `permissionMode`, `toolDenialKind` — a decisão de permissão é **gravada**, não só aplicada.
- `promptSource`, `origin`, `entrypoint` — proveniência de novo, agora persistida.
- `version` — a versão do CLI que escreveu a linha, por linha. É o que torna o formato
  evoluível: um leitor sabe com que geração está lidando.
- `gitBranch`, `cwd` — o contexto de repositório entra na transcrição.
- `attributionSkill` — a skill à qual atribuir aquele turno.

E `sessionId` **e** `session_id` coexistindo é um resíduo visível de migração de formato.

### Os arquivos-irmãos de uma sessão

Ao lado de `<uuid>.jsonl` há uma pasta `<uuid>/`:

```
<uuid>/
  subagents/
    agent-<id>.jsonl        ← a transcrição própria de cada subagente
    agent-<id>.meta.json
  tool-results/
    <id>.txt                ← resultados volumosos, fora da transcrição
```

Duas decisões de arquitetura legíveis daqui:

1. **Cada subagente tem transcrição própria**, não linhas intercaladas na do pai. Combina com
   `agentId` sendo pinado em `turn.step` e `session.compact`.
2. **Resultado grande de ferramenta sai da transcrição** e vira arquivo referenciado. É o
   mesmo princípio de `ToolUseSummary` guardar o registro "sem o volume" em headless
   ([05](05_sistema_tools.md)) — a transcrição fica navegável.

## Sessões em background: `jobs/`

Uma pasta por job, com `state.json`, `timeline.jsonl` e `tmp/`.

`timeline.jsonl` é um log de transição de estado, com exatamente quatro campos por linha:
`{ at, state, detail, text }`. Event sourcing simples e legível.

As chaves de `state.json` dizem bastante sobre o que uma sessão em background é:

```
backend, bgIsolation, bridgeOutboundOnly, bridgeOwnerAccountUuid,
bridgeOwnerOrganizationUuid, bridgeSessionId, children, cliVersion, createdAt, cwd,
daemonShort, detail, firstTerminalAt, inFlight, intent, interactiveLineage,
lastTerminalAt, linkScanOffset, linkScanPath, name, nameSource, output, providerEnv,
respawnFlags, resumeSessionId, sessionId, state, template, tempo, tokens, updatedAt
```

Destaques:
- `children` + `interactiveLineage` — jobs formam **árvore**, e há um caminho de volta até a
  sessão interativa que os originou.
- `respawnFlags` — o job sabe com que flags renascer. Casa com a entrada do `CHANGELOG`
  sobre `/bg` preservar `--mcp-config`, `--settings`, `--add-dir`, `--plugin-dir`.
- `bgIsolation` — o modo de isolamento (worktree), o setting `worktree.bgIsolation` visto em
  [17](17_evolucao_changelog.md).
- `bridge*` — a ponte de Remote Control, com dono por conta e por organização.
- `tokens` — contabilidade de custo por job.

## `file-history/` — o mecanismo de `/rewind`

```
file-history/<session-uuid>/<hash-do-caminho>@v<N>
```

Uma versão por arquivo por revisão, endereçada por hash do caminho, agrupada por sessão.
12 MB aqui, e é a maior pasta depois de transcrições e jobs — o custo do undo.

## `telemetry/` — só o que falhou

Os arquivos seguem o padrão `1p_failed_events.<uuid>.<uuid>.json`. Ou seja: o que é enviado
com sucesso **não é guardado em disco**; o que fica é fila de reenvio do que falhou. Coerente
com o desenho do mod `telemetry` — "uma tentativa, nada em lote"
([10](10_mod_telemetry.md)); a persistência de falha é do lado do CLI, não do mod.

## Outros detalhes observados

- `plans/` guarda um `.md` por plano do plan mode, com nome legível gerado
  (`<slug>-<palavra>-<palavra>.md`). 61 arquivos aqui.
- `sessions/<n>.json` tem duas chaves: um token de peer e o instante de início do processo.
  **Valores não lidos.** É o handshake local entre processos.
- `shell-snapshots/snapshot-zsh-<epoch_ms>-<rand>.sh` — o shell do usuário é *snapshotado*,
  o que explica por que `Bash` herda funções e aliases do perfil mas não o estado entre
  chamadas.
- `backups/.claude.json.backup.<epoch_ms>` — backup rotativo do config global.
- `cache/changelog.md` — o CHANGELOG é baixado e cacheado localmente.
- `plugins/` tem `marketplaces/`, `cache/`, `synced/`, `data/`, `installed_plugins.json`,
  `known_marketplaces.json` — e `synced/` com ids de bucket, o que indica sincronização de
  plugin por conta/organização, não só instalação local.

## Por que isto importa para o harness próprio

O que dá para copiar sem copiar código nenhum:

1. **Transcrição como JSONL com `parentUuid`**: uma linha por evento, árvore por ponteiro de
   pai, `version` em cada linha. Simples de anexar, simples de ler em streaming, evoluível.
2. **Volume fora da transcrição** (`tool-results/`), referenciado por id.
3. **Subagente com transcrição própria**, ligada por id.
4. **Decisão de permissão persistida** (`permissionMode`, `toolDenialKind`), não só aplicada
   — é o que permite auditar depois.
5. **Job como diretório**: estado + timeline de transições + tmp. E `respawnFlags` para que
   reiniciar seja um fato do estado, não uma reconstrução.
6. **Histórico de arquivo endereçado por hash de caminho**, agrupado por sessão.

## Ver também

- [04](04_agent_loop_turn.md) — os campos que aparecem aqui, no contrato
- [17](17_evolucao_changelog.md) — a evolução que produziu essas pastas
- [20](20_implicacoes_harness_capella.md) — o que disso vale para o harness do Capella
