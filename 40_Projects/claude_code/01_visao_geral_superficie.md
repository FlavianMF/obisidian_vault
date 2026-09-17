---
title: Visão geral e superfície do repositório
type: project
tags: [claude-code, oss, licensing, distribution]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

> Ver [[claude-code]] para a nota-conceito e os padrões de harness extraídos desta pesquisa.

# Visão geral: o que é o Claude Code e o que o repositório é

[← Índice](00_indice.md)

## O produto

Ferramenta de codificação agêntica que roda no terminal, no IDE (VS Code, JetBrains), no
desktop, na web (claude.ai/code) e como `@claude` no GitHub. Node 18+ nominal, mas a
distribuição atual não usa Node do usuário.

Canais de instalação, na ordem em que o `README.md` os apresenta:

```bash
curl -fsSL https://claude.ai/install.sh | bash     # macOS/Linux, recomendado
brew install --cask claude-code
irm https://claude.ai/install.ps1 | iex             # Windows, recomendado
winget install Anthropic.ClaudeCode
npm install -g @anthropic-ai/claude-code           # DEPRECADO
```

> **NOTA:** Instalação via npm está deprecada.

O que se vê em disco confirma: o executável é um ELF único de ~230 MB, compilado
(perfil de bundle Bun), com versões antigas mantidas lado a lado para rollback
([16](16_runtime_local_observado.md)).

Documentação oficial: <https://code.claude.com/docs/en/overview>. O domínio antigo
(`docs.claude.com/en/docs/claude-code`) ainda aparece em READMEs de plugins mais velhos
dentro do próprio repo — um resíduo de migração útil de notar quando se segue links.

## O repositório **não** é o código-fonte do produto

Este é o ponto que muda a forma de pesquisar. `LICENSE.md`, na íntegra:

> © Anthropic PBC. All rights reserved. Use is subject to Anthropic's
> [Commercial Terms of Service](https://www.anthropic.com/legal/commercial-terms).

Sem licença open source. E o binário não está aqui: o repositório tem 1153 blobs e 31 MB,
contra 230 MB de executável.

O que o repositório **é**: o canal público de tudo que cerca o produto — extensibilidade,
política, exemplos de deploy, histórico e triagem de issues.

## O inventário, por peso

| Caminho | Blobs | O que contém |
|---|---:|---|
| `mods/` | 923 | Os três mods built-in, com source completo, testes e o `.d.ts` do engine |
| `plugins/` | 149 | 13 plugins oficiais: comandos, agentes, skills, hooks |
| `examples/` | 38 | settings, MDM, gateway (AWS/GCP + Terraform), hook de exemplo |
| `.github/` | 18 | 13 workflows, cinco deles rodando o próprio Claude Code |
| `scripts/` | 8 | Automação de issues, e os wrappers restritos que o agente de CI usa |
| `.claude/`, `.claude-plugin/` | 4 | Os comandos e a marketplace do próprio repo |
| raiz | 6 | `README.md`, `CHANGELOG.md` (718 KB), `LICENSE.md`, `SECURITY.md`, `feed.xml`, `demo.gif` |

E o artefato mais denso de todos, dentro de `mods/`:

**`mods/types/claude-code.d.ts` — 407 KB, 10.772 linhas, 432 tipos exportados.**
É a declaração completa da API de hooks: ~22 substantivos, 84 nomes de evento, 33 hooks
clássicos absorvidos, mais o kit de teste. Não é documentação *sobre* a arquitetura; é a
arquitetura, escrita como contrato ([03](03_event_surface.md)).

O cabeçalho dele diz como foi produzido:

> Written by Claude Code 2.1.273. […] Written by `/plugin-types`; regenerate with that
> command after an update rather than editing.

Ou seja: é **gerado da build**, não mantido à mão. Cada instalação pode escrever o seu.

## O que é público, o que é gerado, o que é fechado

| Camada | Estado |
|---|---|
| Contrato da API de hooks | **Público**, publicado como `.d.ts` (early access) |
| Source dos três mods built-in | **Público**, TypeScript completo com testes |
| Source dos 13 plugins | **Público** |
| Inventário de ferramentas built-in | **Gerado localmente** por `/plugin-types` — não está no repo |
| Loop do agente, prompts de sistema, permissão | **Fechado**, dentro do binário |
| Histórico de mudanças | **Público**, 5.768 entradas |

A linha divisória é coerente: **a superfície de extensão é aberta; a implementação é
fechada.** Um terceiro consegue escrever um mod correto sem ver o engine, porque o contrato
descreve não só as assinaturas mas o comportamento — ordem da cadeia, o que é pinado, o que
é cacheado, o que acontece quando um hook falha.

## O aviso que governa tudo

```
// EARLY ACCESS: this surface may change between releases without notice.
```
`claude-code.d.ts:4`.

Confirmado do lado operacional: o workflow `mod-tests.yml` roda os testes com
`CLAUDE_CODE_ENABLE_FUNCTION_HOOKS: "1"` — a API inteira está atrás de feature flag
([18](18_ci_dogfooding.md)). E o `CHANGELOG` **não menciona** `function hooks`, `hooks module`,
`register(on` nem `engine.create` em nenhuma das 5.768 entradas
([17](17_evolucao_changelog.md)).

Para quem for depender disso: o canal de alerta não é o changelog, é regenerar o `.d.ts` com
`/plugin-types` e comparar.

## Como esta pesquisa foi conduzida

Clone raso pinado em `68ac8bbf0245b615b41517bf8f2b2f35af1ae31d` (2026-09-17T00:11Z), mais
docs oficiais para o que o repo não cobre, mais observação em disco da instalação local
`2.1.274`. Nenhuma afirmação de arquitetura interna vem do binário — ele não foi
desmontado nem descompilado ([21](21_fontes.md), [16](16_runtime_local_observado.md)).

## Ver também

- [02](02_modelo_engine_hooks.md) — o modelo central, e por onde começar
- [00](00_indice.md) — leitura recomendada por objetivo
