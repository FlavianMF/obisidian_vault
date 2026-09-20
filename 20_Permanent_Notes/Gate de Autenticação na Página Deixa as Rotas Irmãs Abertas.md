---
title: Gate de Autenticação na Página Deixa as Rotas Irmãs Abertas
type: trap
tags: [security, frontend, nextjs, app-router, authentication, layout, armadilha]
created: 2026-09-20
provenance: orbita-platform
project: orbita-platform
---

# Gate de Autenticação na Página Deixa as Rotas Irmãs Abertas

## Sintoma

Uma página autenticada renderiza **estado vazio** em vez de pedir login para
quem não tem sessão. Não dá erro, não redireciona, não mostra formulário: só
diz "nenhum item encontrado", como se o usuário tivesse feito login e a lista
estivesse vazia.

Caso real: uma vitrine de parceiros que chamava a API dentro de
`useEffect`, com `.catch(() => setParceiros([]))`. Sem token, o backend
devolvia 401, o `catch` engolia, e a tela mostrava "nenhum parceiro
disponível". O bug passou despercebido por seis etapas de desenvolvimento.

## Causa

O gate de autenticação estava **dentro de uma página** (`if (!token) return
<FormularioDeLogin/>`), não num layout. No App Router do Next (e em qualquer
roteador com layouts aninhados), isso protege exatamente uma rota: a que tem o
`if`. Toda rota **irmã** criada depois — no mesmo grupo, sob o mesmo caminho —
nasce desprotegida, e nada avisa.

Agravante: o `.catch` que transforma falha em lista vazia é idiomático e
correto para erro de rede. Ele só vira encobrimento quando a falha é de
autorização e não existe gate acima para tratá-la.

## Solução

**O gate mora no layout, não na página.** No App Router, um
`layout.tsx` no topo da subárvore cobre todas as páginas dela, inclusive as
que ainda não existem — é o único lugar onde "proteger a área" é uma
afirmação verdadeira em vez de uma convenção que cada página nova precisa
lembrar de seguir.

Sinais de que a armadilha está presente num projeto:

- um grupo de rotas (`(cliente)`, `(app)`, …) **sem** `layout.tsx`, com o
  gate inline na página principal;
- duas páginas irmãs onde uma checa sessão e a outra não;
- um `.catch` que devolve coleção vazia numa chamada que exige autenticação.

O teste que trava a regressão não é "renderiza a lista": é **"sem token,
renderiza o formulário de login E não renderiza o conteúdo"** — as duas
asserções, porque só a primeira passaria com uma tela vazia acidental.

## Generalização

A regra vale além do Next: **autorização pertence ao nó mais alto que cobre
tudo o que ela protege**. Colocá-la num nó folha transforma uma propriedade
estrutural ("esta área exige sessão") numa convenção repetida, e convenção
repetida falha na primeira rota que alguém adiciona com pressa.

É a mesma família de [[Filtro de Tenant Opcional em ORM Vaza Tudo, Não Nega Acesso]]:
nos dois casos a falha é **silenciosa e parece dado legítimo** — lista vazia
ali, lista completa aqui.
