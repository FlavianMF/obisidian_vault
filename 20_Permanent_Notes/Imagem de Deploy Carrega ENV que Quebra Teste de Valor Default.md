---
title: Imagem de Deploy Carrega ENV que Quebra Teste de Valor Default
type: trap
tags: [docker, testing, ci-cd, environment, nextjs, armadilha]
created: 2026-09-20
provenance: orbita-platform
project: orbita-platform
---

# Imagem de Deploy Carrega ENV que Quebra Teste de Valor Default

## Sintoma

A suíte roda dentro de uma imagem Docker do projeto e um punhado de testes
falha — testes de arquivos que a sessão **não tocou**. As mensagens parecem
regressão de verdade (`expected false to be true`, `expected null to be
'http://...'`), e não somem ao rodar o arquivo isolado, o que descarta a
explicação fácil de flakiness por carga.

Caso real: 5 testes de roteamento por Host (`proxy.ts`, Next.js) falhando
numa worktree cujo diff nem chegava perto do arquivo.

## Causa

A imagem usada para rodar os testes era a **imagem de deploy** (homologação),
e ela embute as variáveis de ambiente do ambiente de destino no próprio
`Config.Env`:

```
NEXT_PUBLIC_CONSULTOR_HOST=hml-consultor.researchy.cloud
NEXT_PUBLIC_ADMIN_HOST=hml-admin.researchy.cloud
```

Os testes exercitavam o **fallback** do código
(`process.env.X || 'consultor.localhost'`). Com a variável definida pela
imagem, o `||` nunca cai no default, o código passa a comparar contra o host
de homologação, e nenhuma das reescritas esperadas acontece.

Não é bug do produto e não é regressão: é o ambiente do teste mentindo. O CI
passa porque lá a imagem é outra (ou a env é limpa).

## Diagnóstico em dois comandos

1. Rode o mesmo teste contra o checkout da branch principal, intocado:
   `docker run --rm -v "<repo>/frontend:/app:ro" -v <vol>:/app/node_modules -w /app <imagem> npx vitest run <spec>`.
   Falhou lá também? **É ambiente, não o seu diff.**
2. Veja o que a imagem carrega:
   `docker inspect <imagem> --format '{{range .Config.Env}}{{println .}}{{end}}'`

## Solução

Neutralize as variáveis na execução — string vazia é falsy, então o `||`
volta a valer:

```bash
docker run --rm -e NEXT_PUBLIC_CONSULTOR_HOST= -e NEXT_PUBLIC_ADMIN_HOST= ... npx vitest run
```

Melhor ainda, quando existir: rode a suíte na **imagem de desenvolvimento**,
não na de deploy. Imagem de deploy carrega configuração de destino por
definição — usá-la como runner de teste mistura duas responsabilidades.

## Por que vale registrar

É primo da armadilha de restaurar `process.env` em `afterEach` (atribuir
`undefined` vira a string `"undefined"`, que é truthy), mas vem de **fora do
código de teste**: nada no repositório denuncia a causa. Sem saber onde
olhar, o caminho natural é desconfiar do próprio diff e reescrever código que
estava certo.

Relacionado: [[Notas de Análise Envelhecem em Dias - Reverificar no Código Antes de Apresentar]]
— nos dois casos, a checagem barata é reverificar contra o estado real antes
de concluir.
