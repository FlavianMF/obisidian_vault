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

## Variante: dois wrappers Python, uma classe EMF só

Achado adicional modelando a camada Operational Analysis (2026-08-13):
nem toda distinção de `type_name` corresponde a uma classe EMF
diferente. `OperationalActor` e `OperationalEntity` no
`simplified_api` são duas classes Python **sobre a mesma classe EMF
subjacente** (`Entity`), diferenciadas só por uma flag booleana
(`actor=True/False`) setada no construtor — `OperationalEntity` é
inclusive subclasse Python de `OperationalActor`, mas semanticamente
representam papéis opostos (ator = "geralmente humano, não pode ser
decomposto"; entidade = "pode ser decomposto"). Consequência prática:
**as duas compartilham o mesmo accessor de container raiz**
(`EntityPkg.get_owned_entities()`), mas só `OperationalEntity` expõe
`get_owned_entities()` própria pra aninhamento — um `OperationalActor`
pai não tem esse método (por design, não bug), então tentar aninhar
sob um ator deve falhar explicitamente, não silenciosamente. Vale
conferir isso (visão dupla de uma única classe EMF, via flag) sempre
que uma API de binding EMF/Java-Python expõe duas classes com nomes
parecidos e um dos dois é subclasse Python do outro — não assumir que
são tipos EMF distintos sem checar.

## Implementação de referência

`bridge.create_element` em `src/capella_mcp/bridge.py` (projeto
`capella_mcp`) — branches validadas pra `LogicalComponent`/`la`,
`SystemFunction`/`sa`, `LogicalFunction`/`la` (2026-08-13, espelhando
`SystemFunction`), e `OperationalActivity`/`OperationalActor`/
`OperationalEntity`/`OperationalCapability`, todas em `oa` (2026-08-13,
mesma sessão da camada OA completa). `OperationalCapability` é o único
caso **sem nenhum accessor de aninhamento** — capacidades são sempre
flat no Arcadia, então a branch rejeita `parent_id` com erro explícito
em vez de tentar adivinhar um accessor que não existe. Qualquer outro
`type_name` ainda cai no fallback quebrado
(`get_contents().append()`) até ganhar sua própria branch —
interfaces/exchanges e alocação funcional/operacional continuam sem
branch.

## 🔗 Conexões
- [[Eclipse RCP Headless - workspace URLs Exigem Projeto Importado via -import]]
- [[Capella MBSE]]
- [[Capella Breakdown Diagram - root_id Infere Tipo Concreto, Não o Declarado]]
