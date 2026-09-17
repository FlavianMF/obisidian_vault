---
title: Fontes da pesquisa Claude Code
type: project
tags: [claude-code, sources, references]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Fontes

[← Índice](00_indice.md)

Toda citação desta pesquisa aponta para uma destas fontes. O repositório é um alvo móvel
(o `CHANGELOG.md` muda quase todo dia), então **tudo que vem do repo está pinado no
commit abaixo** — links `blob/<sha>/` em vez de `blob/main/`.

## Pin

| Item | Valor |
|---|---|
| Repositório | <https://github.com/anthropics/claude-code> |
| Branch default | `main` |
| Commit pinado | `68ac8bbf0245b615b41517bf8f2b2f35af1ae31d` |
| Data do commit | 2026-09-17T00:11:55Z |
| Blobs no commit | 1153 |
| Licença | `LICENSE.md` — "© Anthropic PBC. All rights reserved", sujeito aos [Commercial Terms of Service](https://www.anthropic.com/legal/commercial-terms) |
| Versão local usada na observação de runtime | `2.1.274` |
| Data da pesquisa | 2026-09-16 |

Prefixo de permalink usado nesta pesquisa:

```
https://github.com/anthropics/claude-code/blob/68ac8bbf0245b615b41517bf8f2b2f35af1ae31d/<caminho>
```

Para reproduzir localmente:

```bash
git clone --depth 1 https://github.com/anthropics/claude-code
git -C claude-code rev-parse HEAD   # deve bater com o SHA acima
```

Um clone raso basta: nenhuma afirmação aqui depende de histórico do git — o histórico do
produto está no `CHANGELOG.md`, não nos commits.

## Fontes primárias — repositório

| Caminho | Tamanho | Usado em |
|---|---|---|
| `mods/types/claude-code.d.ts` | 407 KB / 10.772 linhas | 02, 03, 04, 05, 07, 13, 14 |
| `mods/README.md` | 5,0 KB | 02, 08, 12 |
| `mods/diff/**` | 779 arquivos | 09 |
| `mods/telemetry/**` | 81 arquivos | 10 |
| `mods/sec-default/**` | 60 arquivos | 11 |
| `plugins/**` | 149 arquivos | 08, 14 |
| `examples/settings/**` | 4 arquivos | 06, 15 |
| `examples/mdm/**` | 6 arquivos | 06, 15 |
| `examples/gateway/**` | 26 arquivos | 13 |
| `examples/hooks/bash_command_validator_example.py` | 1 arquivo | 06 |
| `CHANGELOG.md` | 718 KB | 17 |
| `.github/workflows/**`, `scripts/**` | 26 arquivos | 18 |
| `README.md`, `SECURITY.md`, `LICENSE.md` | — | 01 |

## Fontes primárias — documentação oficial

Base: <https://code.claude.com/docs/en/overview> (o repo aponta para cá; o antigo
`docs.claude.com/en/docs/claude-code` redireciona). Páginas citadas individualmente nos
capítulos que as usam. Docs não são pináveis — data de consulta: 2026-09-16.

## Fonte observacional — runtime local

Máquina do usuário, instalação `2.1.274`. Entram **apenas artefatos que o programa
escreve em disco** (layout de diretório, formato de arquivo, JSON de configuração):
`~/.claude/`, `~/.local/share/claude/versions/`. Usado no capítulo 16.

Fora do escopo por decisão explícita: desmontar, descompilar ou extrair strings do
binário — é produto proprietário. Nenhuma afirmação de arquitetura interna nesta pesquisa
vem do binário; todas vêm do `.d.ts`, do source dos mods, dos docs ou do CHANGELOG.
Também não são transcritos conteúdos de sessão do usuário, nem credenciais.

## Pesquisa irmã

`notes/research/opencode/` — mesmo formato, sobre o harness opencode. Base do comparativo
no capítulo [19](19_comparativo_opencode.md).
