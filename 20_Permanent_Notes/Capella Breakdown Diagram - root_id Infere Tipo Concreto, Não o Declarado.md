---
title: Capella Breakdown Diagram — root_id Infere Tipo Concreto, Não o Declarado
type: trap
tags: [python4capella, capella, sirius, gmf, headless, eclipse]
created: 2026-08-13
provenance: capella_mcp
project: capella_mcp
---

# Capella Breakdown Diagram — root_id Infere Tipo Concreto, Não o Declarado

Continuação de [[Python4Capella get_contents() é Snapshot Desconectado - Containment Real Exige get_owned_X()]]:
mesma família de armadilha (getter genérico vs. accessor real), mas do
lado de gerar diagrama (Sirius breakdown), não de criar elemento.

## Sintoma 1 — `root_id` no componente raiz padrão falha

```
create_diagram(layer="la", type_name="LogicalComponent", root_id=<id do
LogicalComponent raiz padrão de um projeto novo, "Logical System">)
```

```
ValueError: no breakdown diagram known for type LogicalSystem in layer 'la'
```

Mesmo passando `type_name="LogicalComponent"` explicitamente junto —
ele é ignorado.

## Causa

Quando `root_id` é dado, a implementação (`bridge.create_diagram`)
resolve o elemento e **sobrescreve** `type_name` com
`type(root).__name__` pra procurar o mapeamento Sirius certo
(`node_mapping`/`edge_mapping`). O componente raiz que todo projeto
Capella novo cria por padrão ("Logical System", "System", "Physical
System" etc.) não é instância da classe declarada
(`LogicalComponent`/`SystemComponent`/`PhysicalComponent`), é de uma
**subclasse concreta** (`LogicalSystem`, por exemplo) que não está na
tabela de mapeamentos de diagrama — só os tipos "normais"
(`LogicalComponent`, `SystemFunction`, etc.) têm entrada.

## Fix

Pro componente/função raiz padrão de um projeto novo, **não passar
`root_id`** — passar só `type_name`. O caminho sem `root_id` busca
candidatos via `pkg.get_owned_<x>()` (ex.:
`get_logical_component_pkg().get_owned_logical_components()`), que
devolve o elemento raiz **independente da sua subclasse concreta**
(diferente do caminho `root_id`, que casa por nome de classe exato).
Só funciona se houver exatamente um candidato raiz — se houver mais de
um, dá erro "multiple root-level elements found" e aí sim é preciso
`root_id`, mas apontando pra um dos filhos reais (não pro raiz
ambíguo).

## Sintoma 2 — `export_diagram` reporta `files: []` mesmo com sucesso

`export_diagram` chama o exportador headless nativo do Capella
(`org.polarsys.capella.exportRepresentations`), que grava os PNGs num
subdiretório aninhado com nome de projeto Eclipse + arquivo do modelo:

```
<model>_diagram_exports/<project_name>/<model_filename>.aird/*.png
```

Mas `bridge.export_diagram` faz
`out_dir.glob(f"*.{image_format.lower()}")` — **não recursivo**, só na
raiz de `<model>_diagram_exports/`. Resultado: `{"files": []}` mesmo
quando os PNGs existem e estão corretos. `files: []` **não é sinal de
falha** aqui — é um bug de glob no bridge (deveria ser `rglob`), ainda
não corrigido em 2026-08-13.

## Fix / como verificar de verdade

Ignorar `files` na resposta; procurar direto:
`find <output_dir> -name '*.png'` (ou `ls -R`), depois abrir o PNG
específico (visualizador de imagem / `Read` no Claude Code) pra
confirmar o conteúdo do diagrama.

## Generalização

Duas lições reaproveitáveis: (1) quando uma API de diagrama/geração
resolve tipo por **inferência a partir de um id**, desconfiar de
elementos "raiz"/"default" que costumam ser subclasses especializadas
do tipo nominal — prefira o caminho que não depende de resolução por
classe exata quando ele existir. (2) uma lista de arquivos retornada
por uma ferramenta headless pode estar simplesmente errada (bug de
glob/path) sem que a operação subjacente tenha falhado — sempre que
plausível, confirme no filesystem em vez de confiar cegamente no
retorno estruturado.

## Implementação de referência

`bridge.create_diagram` e `bridge.export_diagram` em
`src/capella_mcp/bridge.py` (projeto `capella_mcp`).

## 🔗 Conexões
- [[Python4Capella get_contents() é Snapshot Desconectado - Containment Real Exige get_owned_X()]]
- [[Eclipse RCP Headless - workspace URLs Exigem Projeto Importado via -import]]
- [[Capella MBSE]]
