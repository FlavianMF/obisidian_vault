---
title: Filtro de Tenant Opcional em ORM Vaza Tudo, Não Nega Acesso
type: trap
tags: [prisma, orm, multi-tenant, security, typescript, sql, armadilha]
created: 2026-09-20
provenance: orbita-platform
project: orbita-platform
---

# Filtro de Tenant Opcional em ORM Vaza Tudo, Não Nega Acesso

## Sintoma

Uma rota multi-tenant que parece correta — filtra pelo `tenantId` do ator,
tipa o campo, passa nos testes — devolve **200 com os dados de todos os
tenants** quando o `tenantId` chega ausente. Não é um 403, não é uma lista
vazia, não é erro: é o vazamento completo, com status de sucesso.

O caso que originou a nota: catálogo de parceiros por consultoria, em que
um `consultoriaId?: string` alimentaria `where: { consultoriaId }`.

## Causa

O Prisma (e vários ORMs) trata `undefined` num `where` como **"este filtro
não foi informado"**, não como "não encontra nada". `where: { tenantId:
undefined }` é literalmente `where: {}` — tabela inteira.

O compilador não ajuda: `string | undefined` é um tipo perfeitamente
válido para o campo, e a query roda. O teste tampouco ajuda, porque o
caminho feliz sempre tem o valor preenchido; o caso do campo ausente só
aparece quando um papel novo, um token diferente ou uma desvinculação
posterior entra em cena.

Mesma família do [[Decoder JSON em Go Trata Chave Ausente e Null Como Idêntico]]:
**ausência e "sem restrição" colapsam no mesmo valor**, e o colapso é
silencioso.

## Solução

Não passe o tenant como campo opcional. Passe um **escopo como união
discriminada**, resolvido por um middleware antes da query:

```ts
type EscopoCatalogo =
  | { tipo: 'TODOS' }                                  // admin da plataforma
  | { tipo: 'GLOBAL' }                                 // só o catálogo público
  | { tipo: 'CONSULTORIA'; consultoriaId: string };    // um tenant

function filtroDeTenant(e: EscopoCatalogo): WhereInput {
  switch (e.tipo) {
    case 'TODOS':       return {};
    case 'GLOBAL':      return { consultoriaId: null };
    case 'CONSULTORIA': return { consultoriaId: e.consultoriaId };
  }
}
```

Três consequências que o campo opcional não dá:

1. **Esquecer um caso vira erro de `tsc`**, não vazamento em runtime — e
   `tsc` costuma ser gate bloqueante no CI.
2. **"Sem filtro" passa a ser uma decisão escrita** (`{ tipo: 'TODOS' }`),
   não o efeito colateral de um valor ausente.
3. O escopo vira **parâmetro obrigatório** de toda função do serviço: uma
   chamada nova não compila sem declarar de quem é a visão.

Complementos que valem a pena junto:

- **Resolver o tenant no banco a cada request**, nunca do token nem do
  corpo. O JWT é emitido no login e não reflete uma desvinculação
  posterior; o corpo é do cliente HTTP, e deixar o ator escolher o próprio
  tenant é o vazamento inteiro numa linha.
- **Responder 404, não 403, em acesso cruzado.** O filtro de tenant entra
  no `where` da própria busca, então o registro alheio não existe para
  aquele ator — e um 403 confirmaria que ele existe.
- **Papel nunca é blindagem de tenant.** Um papel em array multivalorado
  (`papeis: Papel[]`) passa por um `requirePapel(...)` mesmo num token que
  não carrega o campo de tenant. O gate correto exige o campo presente.

## Sinal de que você está na armadilha

Procure por `where` montado a partir de um campo que o tipo declara como
opcional, e por gates que checam **papel** sem checar **presença do campo
de tenant**. Um teste que prove a negação precisa forjar o token exatamente
como o servidor o emitiria no caso problemático — não como o caminho feliz.

## Corolário: elegibilidade e escopo são perguntas diferentes

Ao aplicar o escopo discriminado, não colapse **"pode entrar?"** com **"vê o
quê?"**. No caso real, um cliente vinculado a um consultor **sem** organização
é elegível ao produto, mas seu conjunto de tenants é **vazio** — ele enxerga
só o catálogo público.

Tratar conjunto vazio como "sem acesso" puniria o usuário por uma
característica de terceiro (o consultor dele não pertencer a uma organização).
Tratar como "sem filtro" seria o vazamento original. O correto é reconhecer
que são duas decisões: um gate responde a primeira, o escopo responde a
segunda — e `{ in: [] }` é a tradução certa de "nenhum tenant privado", não um
caso degenerado a evitar.

