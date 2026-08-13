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

## Método de extração de node_mapping/edge_mapping real (pra novas entradas em BREAKDOWN_DIAGRAMS)

`bridge.py` tinha um comentário dizendo "see docs/second_brain for the
extraction method" perto de `BREAKDOWN_DIAGRAMS`, mas nenhuma nota
documentava isso até agora (2026-08-13, adicionando entrada nova pra
`OperationalEntity`/`OperationalActor`). Processo que funcionou:

1. Achar o jar certo na instalação Capella local:
   `org.polarsys.capella.core.sirius.analysis_<versão>.jar` (procurar em
   `<capella_install>/plugins/` — atenção, o executável `capella` também
   se chama `capella`, não confundir com o diretório raiz da instalação).
2. Jar é zip — listar/extrair com `zipfile` do Python (não precisa
   `unzip`/`jar` no PATH). Dentro tem `description/*.odesign` — um por
   camada Arcadia (`oa.odesign`, `logical.odesign`, `physical.odesign`,
   `context.odesign` pra SA, `EPBS.odesign`, `common.odesign` com
   definições base compartilhadas).
3. `.odesign` é XML Sirius (Viewpoint Specification Model). Procurar
   `<ownedRepresentations xsi:type="description_2:DiagramDescription"
   name="...">` pelo nome do diagrama (grep case-insensitive pelo domínio,
   ex. "Entity" — não sabia o nome exato de antemão, "Operational Entity
   Breakdown" só apareceu na busca).
4. Dentro do bloco do diagrama certo, achar `<nodeMappings name="...">`
   (o valor de `name` é o `node_mapping`) e `<edgeMappings name="...">`
   (o `edge_mapping`, geralmente auto-referenciando o mesmo nodeMapping
   como source/target pra aresta pai→filho).
5. Cross-check: grep pelos nomes já conhecidos (`OAB_OperationalActivity`,
   `LCB_LogicalComponent`, etc.) no mesmo jar/arquivos confirma que é a
   mesma fonte usada nas entradas existentes — dá confiança que o
   resultado novo é comparável.
6. `domainClass` do `nodeMappings` pode ser um ancestral abstrato (ex.
   `"Component"` pra `Entity`, não `"Entity"` direto) — não é erro, é
   assim que o metamodelo Capella modela (`Entity` extends
   `AbstractConceptItem` extends `cs::Component`). Confirmar via o
   `.ecore` do domínio (`OperationalAnalysis.ecore`,
   `CompositeStructure.ecore`) se parecer estranho, em vez de assumir
   typo.

## Sintoma 3 — mapeamento existe, `create_diagram` não dá erro, mas exporta em branco

Achado 2026-08-13 implementando a entrada `("oa", "OperationalEntity")`
acima: `create_diagram` retornou sucesso (`node_count=1`, sem exceção,
`edge_mapping` com espaço no nome — `"containedIn Mapping"` — funcionou
normalmente, `get_representation_mapping_by_name` casa por string exata).
Mas o PNG exportado saiu quase vazio (~125 bytes vs ~1800 bytes de um
diagrama equivalente que funciona).

Comparando o `.aird` bruto (XML) dos dois `diagram:DSemanticDiagram`, a
diferença fica clara na notação GMF (`notation:Node`):

```xml
<!-- diagrama que funciona -->
<children xmi:type="notation:Node" type="2001" element="...">
  <children xmi:type="notation:Node" type="5002">...</children>  <!-- label -->
  <children xmi:type="notation:Node" type="3003" element="...">   <!-- compartimento -->
    <styles xmi:type="notation:ShapeStyle" .../>
    <layoutConstraint xmi:type="notation:Bounds"/>
  </children>
  <styles xmi:type="notation:ShapeStyle" fontHeight="8" .../>
  <layoutConstraint xmi:type="notation:Bounds" y="100" width="233" height="40"/>
</children>

<!-- diagrama OES (em branco) -->
<children xmi:type="notation:Node" type="2001" element="...">
  <children xmi:type="notation:Node" type="5002">...</children>  <!-- label -->
  <!-- FALTA o type="3003" -->
  <styles xmi:type="notation:ShapeStyle" .../>  <!-- sem fontHeight -->
  <layoutConstraint xmi:type="notation:Bounds" y="100" width="170" height="40"/>
</children>
```

Falta o filho `type="3003"` (compartimento visual) que todo nó dos outros
6 mapeamentos tem. **Não confirmado a fundo** (decisão consciente de não
forçar mais escavação em GMF/Sirius sem retorno garantido), mas hipótese
mais provável: esse `nodeMappings` usa
`semanticCandidatesExpression="service:getOEBScopeBreakdown()"` (chamada
de serviço Java customizada — ver
`OAServices.getOEBScopeBreakdown(EObject)`), diferente dos outros 6
mapeamentos que resolvem candidatos por navegação direta de metamodelo. O
`apply_mapping()` que `bridge.create_diagram` chama (pass 2, ~linha 863)
pra criar o `DNode` manualmente pode não disparar o refresh completo do
Sirius que monta esse compartimento pra mapeamentos com
`semanticCandidatesExpression` baseada em serviço.

**Lição**: "a tool não deu erro" continua não sendo prova de sucesso
completo, nem depois de já ter aprendido isso duas vezes nesta mesma
sessão (containment silencioso, `export_diagram` `files: []`) — dessa
vez o dado (`node_count`) estava certo, mas a *representação visual*
saiu quebrada mesmo assim. Sempre que possível, abrir o artefato final
de verdade (aqui, o PNG) em vez de confiar só no JSON de retorno da
tool, mesmo quando ele não reporta erro nenhum.

## Generalização

Três lições reaproveitáveis: (1) quando uma API de diagrama/geração
resolve tipo por **inferência a partir de um id**, desconfiar de
elementos "raiz"/"default" que costumam ser subclasses especializadas
do tipo nominal — prefira o caminho que não depende de resolução por
classe exata quando ele existir. (2) uma lista de arquivos retornada
por uma ferramenta headless pode estar simplesmente errada (bug de
glob/path) sem que a operação subjacente tenha falhado — sempre que
plausível, confirme no filesystem em vez de confiar cegamente no
retorno estruturado. (3) sucesso sem exceção e contagem de nós/arestas
correta não garante que a peça visual renderizada esteja completa —
mapeamentos cujo `semanticCandidatesExpression` usa uma chamada de
serviço customizada (em vez de navegação direta de metamodelo) merecem
verificação visual extra antes de considerar "funcionando".

## Implementação de referência

`bridge.create_diagram` e `bridge.export_diagram` em
`src/capella_mcp/bridge.py` (projeto `capella_mcp`).
`BREAKDOWN_DIAGRAMS` (~linha 138) tem 9 combinações hoje, incluindo
`("oa", "OperationalEntity")`/`("oa", "OperationalActor")` (adicionadas
2026-08-13, ver Sintoma 3 pra limitação conhecida de renderização).

## 🔗 Conexões
- [[Python4Capella get_contents() é Snapshot Desconectado - Containment Real Exige get_owned_X()]]
- [[Eclipse RCP Headless - workspace URLs Exigem Projeto Importado via -import]]
- [[Capella MBSE]]
