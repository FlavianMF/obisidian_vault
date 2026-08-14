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
6 mapeamentos tem.

**Tentativa de fix (2026-08-13, sessão seguinte) — testada e descartada**:
hipótese era que esse `nodeMappings` usa
`semanticCandidatesExpression="service:getOEBScopeBreakdown()"` (chamada
de serviço Java customizada — ver `OAServices.getOEBScopeBreakdown(EObject)`),
diferente dos outros 6 mapeamentos (navegação direta de metamodelo), e que
`apply_mapping()` (usado em `create_diagram` pass 2) não disparava o
refresh completo do Sirius que monta esse compartimento. Li
`simplified_api/diagram.py` inteiro (extraído do addon) — confirmado: não
existe **nenhuma** chamada de refresh/canonical-sync/arrange em lugar
nenhum do `Python4Capella` (`diagram.py`, `capella.py`, `Sirius_API.py`,
`EMF_API.py`, `Capella_API.py` — grep completo, zero ocorrência fora de um
`refresh()` de recurso Eclipse não relacionado a diagrama). `diagram.py`
já referencia `org.eclipse.sirius.business.api.dialect.DialectManager.
INSTANCE` (em `create_representation`); essa mesma classe expõe
`.refresh(DRepresentation, boolean, IProgressMonitor)` — testei adicionar
essa chamada no início da transação do pass 2 de `create_diagram`
(bridge.py), antes do loop de criação de nós. **Rodou sem erro nenhum**
(prova de que executou de verdade — se tivesse falhado, a chamada MCP
inteira teria retornado `{"error": ...}`), mas o XML resultante ficou
**byte-a-byte idêntico** ao caso sem o refresh — `type="3003"` continuou
faltando, PNG continuou em branco. Revertido, sem deixar rastro no
bridge.py.

Isso **descarta** "falta uma chamada de refresh/sync" como causa raiz — o
canonical synchronizer real do Sirius (o que de fato monta o
compartimento pros outros 6 tipos) dispara sozinho em
`commit_transaction()`, de forma idêntica pros 9 tipos de diagrama (nada
no nível Python4Capella diferencia por tipo); forçar mais um `refresh()`
manual não muda o resultado porque o sync automático já rodou e já
decidiu não criar o compartimento pra esse mapeamento específico. Causa
raiz mais provável agora: a própria definição de **estilo** (`<styles>`)
do `nodeMappings name="OEB_OperationalEntities"` no `oa.odesign` é
genuinamente diferente/mais simples da de `OAB_OperationalActivity` — não
investigado a esse nível (precisaria comparar as sub-tags `<styles>`/
`conditionnalStyles`/`subNodeMappings` dos dois mapeamentos lado a lado
no XML). Não tentado mais nada além disso por decisão consciente — ver
próxima seção.

**Lição**: "a tool não deu erro" continua não sendo prova de sucesso
completo, nem depois de já ter aprendido isso duas vezes nesta mesma
sessão (containment silencioso, `export_diagram` `files: []`) — dessa
vez o dado (`node_count`) estava certo, mas a *representação visual*
saiu quebrada mesmo assim. Sempre que possível, abrir o artefato final
de verdade (aqui, o PNG) em vez de confiar só no JSON de retorno da
tool, mesmo quando ele não reporta erro nenhum. E uma segunda lição:
"a chamada Java rodou sem exceção" também não é prova de que ela teve
o efeito pretendido — só prova que ela é sintaticamente/semanticamente
válida no ponto onde foi chamada.

**Continuação (2026-08-14, terceira sessão) — hipótese "raiz vira nó" testada e também descartada**

Comparando `oa.odesign` (`OEB_OperationalEntities`) lado a lado com
`logical.odesign`/`physical.odesign`/`EPBS.odesign` (`LCB_LogicalComponent`,
`PCB_PhysicalComponent`, `CIBD_ConfigurationItem`) — os 4 mapeamentos que
têm `conditionnalStyles predicateExpression="aql:self = container"` entre
os 9 tipos de `BREAKDOWN_DIAGRAMS` — achado: **todos os 4** têm essa
condicional (não é exclusiva do OEB), mas só o OEB está quebrado. Os
outros 3 exportam PNG normal (confirmado abrindo o arquivo, ex. 1224
bytes com caixas+ícone+label visíveis pra "Estrutura IHM de Velocidade").
Então "a raiz devia aparecer como nó, e `create_diagram` sempre pula a
raiz" (a hipótese óbvia lendo essa condicional) não explica sozinha o bug
— senão LCB/PCB/CIBD também estariam quebrados.

Testado ao vivo mesmo assim, contra `car_hmi.aird`: `apply_mapping`
manual da própria raiz ("Veículo") como nó extra no diagrama OES quebrado.
Funcionou sem erro (nó criado, `getOwnedDiagramElements()` confirmou 2
`DNode`s depois) — mas o nó da raiz saiu com o **mesmo** `type="2001"`
sem `type="3003"`, idêntico ao nó já existente. **Hipótese descartada.**
Testado também `hide()` + `reveal()` (helpers de
`simplified_api/diagram.py`, via `HideFilterHelper`) pra forçar o GMF a
recriar a view do zero — mesmo resultado, sem `3003`.

O que de fato distingue `OEB_OperationalEntities` dos outros 8 mapeamentos
(incluindo os outros 3 que compartilham a condicional `self = container`):
`semanticCandidatesExpression="service:getOEBScopeBreakdown()"` — chamada
de serviço **não recursiva/sem `self.`**, diferente do padrão
`service:self.<getter>()` que todos os outros 8 usam (inclusive
LCB/PCB/CIBD, que usam `service:self.getCBComponentSemanticCandidates()`)
— e `domainClass="Component"` (interface genérica) em vez do nome de
classe concreta. Esse é o suspeito mais forte hoje pra causa raiz, mas
**não confirmado** no nível de exceção Java — só um debugger anexado à
JVM headless conseguiria confirmar de verdade, fora de escopo pro nível
de abstração deste bridge. Conclusão prática: **é um limite genuíno do
Sirius headless pra esse mapeamento específico**, não um bug no
`create_diagram`/`bridge.py` em si — documentado como tal direto no
código (`BREAKDOWN_DIAGRAMS[("oa","OperationalEntity")]`, comentário
extenso) em vez de continuar tentando "consertar" no nível Python.

## `delete_diagram` — tool nova (2026-08-14)

Pra permitir limpar diagramas quebrados/de teste sem editar `.aird` na
mão: `bridge.delete_diagram(model_path, diagram_uid)`, chama
`org.eclipse.sirius.business.api.dialect.DialectManager.INSTANCE.
deleteRepresentation(descriptor, session)` diretamente (mesma classe que
`create_representation` do `simplified_api/diagram.py` já usa pra criar —
só não tem wrapper pra deletar). `descriptor` é o
`.get_java_object()` do wrapper `Diagram` (retorna o
`DRepresentationDescriptor`, não a `DRepresentation` — atenção pra não
confundir com `.get_java_object().getRepresentation()`, usado em
`create_diagram` pra pegar a `DDiagram` de dentro do descriptor).
Confirmado ao vivo: deletou as duas "Estrutura do Veículo (OES)" de teste
do `car_hmi.aird`.

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

`bridge.create_diagram`, `bridge.export_diagram` e `bridge.delete_diagram`
em `src/capella_mcp/bridge.py` (projeto `capella_mcp`).
`BREAKDOWN_DIAGRAMS` (~linha 138) tem 9 combinações hoje, incluindo
`("oa", "OperationalEntity")`/`("oa", "OperationalActor")` (adicionadas
2026-08-13, ver Sintoma 3 pra limitação conhecida de renderização).

## 🔗 Conexões
- [[Python4Capella get_contents() é Snapshot Desconectado - Containment Real Exige get_owned_X()]]
- [[Eclipse RCP Headless - workspace URLs Exigem Projeto Importado via -import]]
- [[Capella MBSE]]
