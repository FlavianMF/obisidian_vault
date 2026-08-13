---
title: Python4Capella get_contents() é Snapshot Desconectado — Containment Real Exige get_owned_<X>()
type: trap
tags: [python4capella, capella, emf, eclipse, ease, containment, py4j]
created: 2026-08-13
provenance: capella_mcp
project: capella_mcp
---

# Python4Capella get_contents() é Snapshot Desconectado — Containment Real Exige get_owned_<X>()

Continuação de [[Eclipse RCP Headless - workspace URLs Exigem Projeto Importado via -import]]:
mesmo com o workspace/projeto certos e o script rodando sem exceção,
criar um elemento novo via `simplified_api` pode retornar sucesso (id
válido) e **não persistir nada** — falha silenciosa, não erro.

## Sintoma

```python
model.start_transaction()
el = SystemFunction()
el.set_name("Exibir velocidade do carro")
container.get_contents().append(el)   # parece certo, é o "getter genérico"
model.commit_transaction()
model.save()
```

Isso roda sem exceção. O objeto retornado tem `id` válido, mas:
- `get_label()` no objeto recém-criado já vem vazio/errado na mesma
  chamada (primeiro sinal de que algo está errado antes mesmo de
  reabrir o modelo);
- numa chamada **separada** que reabre o `.aird` do zero, o elemento
  simplesmente não existe.

## Causa

`EObject.get_contents()` (herdado por todo elemento do metamodelo)
retorna uma **cópia Python-side desconectada** de `eContents()` — útil
pra leitura/iteração, mas `.append()` nela nunca chega a tocar a árvore
EMF real. Cada classe de container do metamodelo Arcadia expõe, em vez
disso, um accessor **específico do tipo** que devolve a `EList` viva de
verdade, com `.add()` que efetivamente registra containment:

- `LogicalArchitecture.get_logical_component_pkg().get_owned_logical_components()`
  (root) — ou o próprio `get_owned_logical_components()` de outro
  `LogicalComponent` pai, pra aninhar.
- `SystemAnalysis.get_system_function_pkg().get_owned_system_functions()`
  (root) — mas pra aninhar uma `SystemFunction` sob outra, o accessor
  **muda de nome**: é `Function.get_owned_functions()` direto no pai
  (sem pkg intermediário) — não confundir os dois.
- Padrão se repete por camada/tipo: `OperationalActivityPkg.get_owned_operational_activities()`,
  `LogicalFunctionPkg.get_owned_logical_functions()`, etc.

## Fix

Nunca usar `container.get_contents().append(el)` pra criar. Resolver o
accessor `get_owned_<X>()` certo pro tipo específico sendo criado. Se a
doc/stub da `simplified_api` não deixar claro qual é (ou não documentar
nesting), **ler o `capella.py` real gerado**, extraído do jar do addon
(`org.eclipse.python4capella_<versão>.jar!/zips/Python4Capella.zip` —
ver nota linkada acima) em vez de adivinhar: `grep -n "class <Tipo>Pkg\|get_owned_"`
nele mostra o nome exato do método e se retorna `List[<Tipo>]` real.

E depois de criar: **sempre verificar com uma chamada separada** (fresh
open + list/get), nunca confiar só no retorno da própria chamada de
criação — sucesso falso e sucesso real são indistinguíveis na resposta
imediata.

## Generalização

Vale pra qualquer API de binding EMF/Java-Python (não só python4capella):
getters "genéricos" de uma classe-base (`EObject`, `CapellaElement`) que
parecem convenientes pra containment costumam ser projeções/snapshots
de leitura; a operação de escrita real vive num accessor mais
específico e menos óbvio, normalmente nomeado por convenção
(`get_owned_<algo_no_plural>`) mas variando por tipo — não dá pra
assumir que existe um único container genérico pra todos os tipos.

## Implementação de referência

`bridge.create_element` em `src/capella_mcp/bridge.py` (projeto
`capella_mcp`) — branch validada pra `LogicalComponent`/camada `la`,
`SystemFunction`/camada `sa`, e `LogicalFunction`/camada `la`
(adicionada 2026-08-13, espelhando `SystemFunction` — mesma classe
base `Function`, mesmo padrão `get_<x>_pkg().get_owned_<x>()` na raiz
e `get_owned_functions()` compartilhado pro caso aninhado). Qualquer
outro `type_name` ainda cai no fallback quebrado
(`get_contents().append()`) até ganhar sua própria branch —
interfaces/exchanges e alocação funcional continuam sem branch.

## 🔗 Conexões
- [[Eclipse RCP Headless - workspace URLs Exigem Projeto Importado via -import]]
- [[Capella MBSE]]
- [[Capella Breakdown Diagram - root_id Infere Tipo Concreto, Não o Declarado]]
