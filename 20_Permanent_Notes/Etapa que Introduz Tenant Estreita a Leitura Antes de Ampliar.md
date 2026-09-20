---
title: Etapa que Introduz Tenant Estreita a Leitura Antes de Ampliar
type: pattern
tags: [multi-tenant, security, migration, dev-workflow, project-planning, incremental-delivery]
created: 2026-09-20
provenance: orbita-platform
project: orbita-platform
---

# Etapa que Introduz Tenant Estreita a Leitura Antes de Ampliar

## O problema do estado intermediário

Entrega incremental fatia uma mudança grande em etapas mescláveis, cada uma
validada e colocada em produção sozinha. Isso é bom — até a fatia do meio
**introduzir um vazamento que nem a versão antiga nem a final têm**.

Caso real: um recurso antes global (catálogo de parceiros, visível a todo
cliente autenticado) ganhou um tenant opcional. O plano era:

- **Etapa A**: criar o tenant e o CRUD por tenant.
- **Etapa B**: criar o gate de audiência ("só cliente com vínculo ativo") e
  ampliar a leitura para "global ∪ tenants do cliente".

Entre A e B, a leitura pública continuaria sendo "todos os registros ativos".
No instante em que o primeiro registro com tenant fosse cadastrado — e a
Etapa A existe justamente para permitir isso —, **o catálogo privado de uma
consultoria apareceria para todos os clientes**. Nenhum teste falharia: o
comportamento "listar todos os ativos" continuava exatamente como
especificado na etapa anterior.

## A regra

**Ao adicionar tenant a um recurso antes compartilhado, a etapa que cria o
tenant estreita a leitura pública; só a etapa que traz o gate a amplia.**

Concretamente, na Etapa A a vitrine passou a filtrar `tenantId IS NULL`
(apenas o catálogo global). Isso é *mais* restrito que o comportamento
anterior e do que o final — e é justamente o ponto: o estado intermediário
deve ser o mais fechado dos três, nunca o mais aberto.

O custo é quase zero (um caso a mais no escopo de leitura) e a decisão
precisa ser **registrada na nota da etapa**, senão a Etapa B a "corrige" sem
entender por que existia.

## Generalizando

A mesma forma aparece sempre que uma dimensão de autorização nasce antes do
gate que a usa:

- coluna de visibilidade nova antes da tela que a respeita;
- papel novo antes do middleware que o restringe;
- campo de organização antes do filtro de organização.

A pergunta que expõe o caso: **"se esta etapa for para produção sozinha e
alguém usar exatamente a capacidade que ela acabou de criar, quem passa a ver
o quê?"** Se a resposta muda para pior, feche antes de abrir.

Relacionado: [[Filtro de Tenant Opcional em ORM Vaza Tudo, Não Nega Acesso]],
[[Plano de Fase em Etapas Mescláveis]],
[[Nota de Conclusão de Etapa é Entregável, Não Relatório]].
