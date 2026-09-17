---
title: Fachada Nomeada do Mundo em vez de Passar o Engine
type: pattern
tags: [architecture, facade-pattern, testing, plugin-api, capability]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

# Fachada Nomeada do Mundo em vez de Passar o Engine

Quando um componente recebe um objeto-mundo grande (`$`, um `client`, um contexto), **não o
propague**. No ponto de entrada, construa uma fachada tipada com exatamente os membros que
você usa, cada um delegando a uma chamada do mundo, e passe a fachada para todo o resto.

É o que o mod `diff` do [[claude-code]] faz, e é a decisão estrutural dos seus 779 arquivos.
No hook `session.start`:

```ts
await bind({
  now:      () => $.clock.now(),
  run:      (argv, init) => $.process.run(argv, init),
  readFile: path => $.fs.read(path),
  storeGet: key => $.store.get(key),
  openPane: pane => $.ui.open(pane),
  // ... 19 membros no total
}, e.cwd)
```

E o tipo é documentado como *"o engine como o `session.start` o ligou a partir do seu `$`,
cada membro escrito `$.noun.event(...)` ali; usado por todo hook, timer e aperto posterior"*.

**Três ganhos de uma vez:**

1. **A superfície de capacidade do componente vira um artefato legível.** Dá para ler o tipo
   `Host` e saber tudo que o plugin pode fazer no mundo — 19 chamadas, nada mais. Isso é
   documentação, revisão de segurança e citação acadêmica de graça.
2. **O resto do código não conhece o engine.** As centenas de funções abaixo tomam `Host`.
   Trocar a implementação por baixo não toca em nada acima.
3. **Resolve o problema de tempo de vida.** `$` só existe *dentro* de um hook; um timer que
   dispara 300 ms depois não tem um. A fachada capturada tem.

O terceiro ponto é o que costuma passar despercebido e é o que força a decisão: qualquer
harness com trabalho assíncrono fora do dispatch precisa de alguma forma disto.

**Como aplicar** num harness próprio: definir a fachada **antes** de escrever o resto, e
tratar acrescentar um membro a ela como uma decisão consciente — é literalmente ampliar a
capacidade do componente.

Ver também: [[Toda Chamada na API é um Evento Interceptável]],
[[Teste como Plugin no Fundo da Cadeia]].
