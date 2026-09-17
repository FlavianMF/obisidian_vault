---
title: claude-code
type: concept
tags: [ai-agent, cli, harness, agent-architecture, plugin-api, llm]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

# claude-code

Ferramenta de codificação agêntica da Anthropic —
[github.com/anthropics/claude-code](https://github.com/anthropics/claude-code),
docs em code.claude.com/docs. **Software proprietário** (© Anthropic PBC, Commercial ToS):
o binário é um ELF único de ~230 MB (perfil de bundle Bun), e o repositório público **não**
contém o código-fonte do produto.

O que o repositório contém, e é o que o torna estudável:

- `mods/types/claude-code.d.ts` — **407 KB, 10.772 linhas, 432 tipos**: o contrato completo
  da API de hooks. 19 substantivos em `$`, 84 nomes de evento, 33 hooks clássicos absorvidos,
  mais o kit de teste. Gerado da build pelo comando `/plugin-types`, não mantido à mão.
- `mods/` — três plugins built-in com source completo e testes: `diff` (779 arquivos),
  `telemetry` (81), `sec-default` (60).
- `plugins/` — 13 plugins oficiais. `examples/` — settings, MDM, gateway LLM.
- `CHANGELOG.md` — 718 KB, 397 versões, 5.768 entradas.

Segundo estudo de caso de harness deste projeto, depois de [[opencode]]. A licença torna os
padrões **estudáveis mas não reutilizáveis como código**.

## Arquitetura em uma frase

Um plugin é um `register(on, options)` que engancha eventos como funções `($, e, next)`;
`$` é o mundo inteiro (fs, processo, rede, modelo, ferramenta, UI, MCP), **e toda chamada em
`$` é ela própria um evento** que os hooks acima veem, reescrevem, negam (`{ deny }`) ou
respondem sozinhos (`{ value }`); a cadeia tem cinco tiers de autoridade
(`prepend`, `user`, `append`, `builtin`, `core`), do mais externo ao mais interno.

## Padrões extraídos (notas atômicas)

- [[Toda Chamada na API é um Evento Interceptável]]
- [[Autoridade por Assento na Cadeia de Hooks]]
- [[Fachada Nomeada do Mundo em vez de Passar o Engine]]
- [[Teste como Plugin no Fundo da Cadeia]]
- [[Contrato de API que Documenta Comportamento e Custo]]
- [[Proveniência como Dado de Primeira Classe]]
- [[Repo Público sem o Source do Produto]] (trap)

## Outras decisões de design notáveis

- **Compactação é evento de primeira classe** (`session.compact`): `trigger` inclui
  `precompute` (compactar antes de precisar); o hook reescreve `instructions` ou `messages`
  na descida, na subida, ou devolve `{ skip }`. E **"não existe string de resumo: o resumo é
  uma mensagem"** — compactação produz transcrição, não um campo especial.
- **A transcrição nunca é reescrita por plugin.** Um hook de `turn.complete` que devolve
  texto diferente mostra esse texto *abaixo* da resposta; o registro fica intacto. Mesmo
  princípio em `turn.step`: o valor de um hook muda o que os hooks acima leem, nunca o que o
  engine streamou.
- **Anti-recursão no engine, não na disciplina do autor**: um subagente que um hook criou
  por `$.agent.spawn` pula aquele hook nos seus passos; um `$.config.set` de um plugin não é
  visto pelos hooks daquele plugin.
- **Falha de hook é isolada**: sem `.catch`, um hook que falha ou estoura o orçamento
  simplesmente não existe para aquele dispatch. "Um plugin quebrado nunca bloqueia um prompt."
- **Ambiente do plugin sem Node e sem DOM**: acesso ao mundo só via `$` — é isso que torna
  todo acesso enganchável e auditável.

## O que o CHANGELOG diz sobre custo de engenharia

52% das 5.768 entradas são `Fixed`. Concentração: subagente/agente (696 menções), IDE (636),
background (434), MCP (411), permissão (338). **O loop de um agente não é o problema difícil;
o segundo agente é** — e as superfícies externas (IDE, Windows, Remote Control, providers)
somam mais que o núcleo.

## Pesquisa completa

`40_Projects/claude_code/` (22 capítulos) — espelho de `notes/research/claude_code/` no
projeto `projetos_ita`. Repo pinado em `68ac8bbf0245b615b41517bf8f2b2f35af1ae31d`.
