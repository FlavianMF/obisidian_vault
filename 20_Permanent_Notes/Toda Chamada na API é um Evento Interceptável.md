---
title: Toda Chamada na API é um Evento Interceptável
type: pattern
tags: [agent-architecture, api-design, plugin-api, middleware, harness]
created: 2026-09-17
provenance: projetos_ita
project: projetos_ita
---

# Toda Chamada na API é um Evento Interceptável

Num harness extensível, **não crie duas superfícies** — uma "API que o plugin chama" e outra
"eventos que o plugin escuta". Faça a chamada **ser** o evento.

No [[claude-code]]: quando um plugin chama `$.fs.write(...)`, isso é um dispatch que atravessa
a cadeia de hooks. Os hooks acima dele podem passar adiante (`next(e)`), reescrever
(`next({...e, ...})`), recusar (`{ deny }`) ou responder no lugar (`{ value }`). O core é
apenas o elo mais interno — a implementação. O contrato diz isso literalmente: *"as chamadas
em `$` que o host serve, como eventos: `e` é o argumento da chamada quando ela cruza para o
host, e toda uma delas é enganchável pelo nome e por `on('*')`"*.

**Por quê:** essa inversão colapsa quatro problemas normalmente separados num mecanismo só.

| Problema | Solução, sem mecanismo novo |
|---|---|
| Auditar tudo que um plugin faz | `on("*")` |
| Sandboxar um plugin | um hook acima dele nega certos eventos |
| Simular o mundo num teste | hooks abaixo do plugin respondem de memória ([[Teste como Plugin no Fundo da Cadeia]]) |
| Interceptar uma capacidade nova | já dá: o evento existe porque a chamada existe |

O contraste com [[opencode]] é direto: lá os hooks são uma **lista fixa** de pontos de
intercepção (`tool.execute.before/after`, `permission.ask`, `chat.params`…), e a superfície
de automação real é a API HTTP. Cada capacidade nova que alguém queira interceptar exige um
hook novo no engine. Aqui não exige nada.

**Como aplicar:** desenhe a superfície do harness como `<substantivo>.<verbo>` (`fs.read`,
`process.run`, `model.complete`, `tool.call`), implemente o despacho como cadeia de
middleware, e **não dê ao plugin nenhum acesso ao mundo fora dessa superfície** — sem `fs`,
sem `process`, sem rede direta. A ausência de saída lateral é o que torna a garantia real.

Ver também: [[Autoridade por Assento na Cadeia de Hooks]],
[[Fachada Nomeada do Mundo em vez de Passar o Engine]].
