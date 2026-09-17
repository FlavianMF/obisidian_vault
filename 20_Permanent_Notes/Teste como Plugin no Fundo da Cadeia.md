---
title: Teste como Plugin no Fundo da Cadeia
type: pattern
tags: [testing, mocking, agent-architecture, plugin-api]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

# Teste como Plugin no Fundo da Cadeia

Se toda capacidade do sistema é um evento numa cadeia
([[Toda Chamada na API é um Evento Interceptável]]), então **o teste não precisa de framework
de mock**: ele se registra como o elo mais baixo da cadeia e *é* o mundo.

É o desenho de `claude-code/testing` no [[claude-code]]:

> Um teste recebe o próprio `$` do engine e o `on` de um plugin. Cada chamada em `$` é uma que
> o engine faz, através de cada hook do mod carregado como ele é distribuído. Os hooks que o
> teste registra com `on` sentam **abaixo** do mod, onde o resto do mundo estaria, e **nada
> fica abaixo deles**: uma chamada que eles deixam sem resposta lança, nomeando o evento.

A última cláusula é o detalhe que faz funcionar: **não respondido = erro nomeado**, em vez de
`undefined` silencioso. O teste falha dizendo qual evento ninguém atendeu.

```ts
tier('builtin')                       // o teste declara o ASSENTO do que testa
mock.clock(on)                        // relógio em memória
on('process.run', () => ({ value: { exitCode: 128, stderr: 'fatal: not a git repository' } }))
await $.session.start({ ... })        // ser o engine
const { text } = await $.command.run({ command: 'diff', ... })   // ser o usuário
```

**Peças que valem copiar:**

- **`tier(...)`**: o teste declara em que tier o componente carrega, porque o assento muda o
  comportamento ([[Autoridade por Assento na Cadeia de Hooks]]).
- **Relógio controlado**: `clock.advance(ms)` resolve cada espera vencida na ordem em que
  vence, e o que uma espera iniciou roda antes de a próxima resolver; `clock.settle()` deixa
  ver o que um dispatch fez antes de responder, sem o relógio andar. É o que torna testável
  código com debounce, coalescência e poll — que é a maior parte de um plugin de UI.
- **`plugins: [...]`** carrega plugins inline ao lado do que está sob teste: permite testar
  **interação entre tiers** (por exemplo, política de organização contra um plugin hostil).
- **Teste de custo, não só de comportamento.** O `mods/diff` tem um caso chamado *"git runs at
  the built-in's moments and no others"*, que conta os processos disparados entre pontos do
  roteiro. Num harness onde plugins rodam no caminho quente, isso impede degradação invisível.

**Precondição:** este padrão só existe se o componente não tiver saída lateral para o mundo
(sem `fs`, sem `process`, sem rede direta). É o retorno do investimento feito em
[[Toda Chamada na API é um Evento Interceptável]].
