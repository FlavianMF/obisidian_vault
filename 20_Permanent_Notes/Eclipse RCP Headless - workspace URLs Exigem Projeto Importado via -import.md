---
title: Eclipse RCP Headless - workspace:// URLs Exigem Projeto Importado via -import
type: trap
tags: [eclipse, ease, rcp, capella, python4capella, headless, commandline]
created: 2026-08-12
provenance: capella_mcp
project: capella_mcp
---

# Eclipse RCP Headless - workspace:// URLs Exigem Projeto Importado via -import

Continuação de [[Addons de Scripting Eclipse (EASE) Não São Pip-Instaláveis]]:
mesmo já sabendo que um addon EASE só roda via CLI headless do produto
(`<produto> -application ... -appid ...`), o comando mais óbvio ainda
quebra contra uma instalação real. Confirmado ao vivo contra Capella 7.1.0
+ python4capella 1.4.1.

## Sintoma

Comando aparentemente correto (documentação do addon, ex. python4capella,
mostra exatamente isso):

```
./capella -nosplash -consolelog \
  -application org.polarsys.capella.core.commandline.core \
  -appid org.eclipse.python4capella.commandline \
  -data <workspace> workspace:/meu_script.py
```

Contra um `-data <workspace>` **fresco/vazio** (workspace efêmero por
chamada, comum em arquitetura headless-per-call), isso falha em duas
camadas sucessivas:

1. `java.lang.IllegalArgumentException: Path must include project and
   resource name: /meu_script.py` — a URL `workspace://` do EASE exige
   `workspace:/<projeto>/<recurso>`, não um arquivo solto na raiz do
   workspace. Corrigir o path pra incluir uma pasta-projeto
   (`workspace:/proj/meu_script.py`) troca o erro por:
2. `org.eclipse.core.internal.resources.ResourceException: Resource
   '/proj/meu_script.py' does not exist` — mesmo que a pasta `proj/` com
   um `.project` válido exista fisicamente em disco dentro do `-data`,
   o Eclipse **não auto-descobre/registra** projetos soltos no workspace
   ao subir. `refresh.workspace.on.startup=true` (via
   `.metadata/.plugins/org.eclipse.core.runtime/.settings/org.eclipse.core.resources.prefs`)
   não resolve a tempo do job do `-appid` rodar.

## Fix

O mecanismo "core" por trás de `-application
org.polarsys.capella.core.commandline.core` (documentado no jar
`org.polarsys.capella.commandline.doc`, não na doc do addon) expõe
`-import "path1|path2"`: lista de diretórios de projeto Eclipse
(separados por `|`) importados pro workspace **antes** do job do
`-appid` rodar. Com isso:

```
./capella -nosplash -consolelog \
  -application org.polarsys.capella.core.commandline.core \
  -appid org.eclipse.python4capella.commandline \
  -data <workspace> \
  -import "<path>/proj|<path>/Python4Capella" \
  workspace:/proj/meu_script.py
```

`<path>/proj` = pasta com `.project` contendo o script gerado.
`<path>/Python4Capella` = ver próxima seção.

## Trap específica do python4capella: de onde tirar o projeto Python4Capella

Todo script gerado usa `include('workspace://Python4Capella/simplified_api/capella.py')`
pra ganhar `CapellaModel`/`SystemEngineering`. Isso pressupõe um projeto
chamado `Python4Capella` já presente no workspace — mas ele **não vem
pronto em disco em lugar nenhum confiável por padrão**. Ele só existe no
workspace de um usuário porque a GUI do Capella o auto-importa no
primeiro launch (comportamento de onboarding). Num ambiente 100%
headless (imagem Docker que só roda o instalador p2 director, nunca a
GUI; ou qualquer invocação puramente via commandline), esse onboarding
nunca roda — o projeto simplesmente não existe.

A fonte real e portável está **dentro do próprio jar do plugin**:
`plugins/org.eclipse.python4capella_<versão>.jar!/zips/Python4Capella.zip`.
Esse zip interno já tem `.project`, `simplified_api/`, `java_api/`,
`utilities/` na raiz (é o conteúdo do projeto direto, sem pasta
`Python4Capella/` envolvendo). Passar esse `.zip` bruto direto pro
`-import` **não funciona limpo** — importa parcial e deixa o processo
pendurado além do job. O que funciona: extrair o zip pra um diretório
**nomeado literalmente `Python4Capella`** em disco, e passar o *caminho
do diretório* (não do zip) pro `-import`.

```python
import zipfile, io
with zipfile.ZipFile(plugin_jar_path) as jar, jar.open("zips/Python4Capella.zip") as inner:
    with zipfile.ZipFile(io.BytesIO(inner.read())) as project_zip:
        project_zip.extractall(target_dir_named_Python4Capella)
```

## Generalização

Qualquer invocação headless/commandline de um produto Eclipse RCP
(Capella ou outro) que use `include()`/`workspace://` do EASE precisa
que o script, e qualquer projeto que ele `include()`, estejam
registrados via `-import` no workspace daquela invocação — um workspace
`-data` efêmero/novo não auto-descobre pastas-projeto que já estão em
disco. Isso vale mesmo com o `.project` correto presente.

## Nota lateral

No Linux não existe binário `capellac` separado (diferente do Windows,
`capellac.exe`) — desde Capella 5.0 o mesmo `./capella` serve GUI e
headless. Alguma doc/comentário por aí ainda menciona `capellac` pro
Linux por engano.

## Implementação de referência

`_ensure_python4capella_project()` + `_run_script()` em
`src/capella_mcp/bridge.py` (projeto `capella_mcp`).

## 🔗 Conexões
- [[Addons de Scripting Eclipse (EASE) Não São Pip-Instaláveis]]
- [[Capella MBSE]]
