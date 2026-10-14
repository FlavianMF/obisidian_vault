---
title: Importador CSV do JIRA - Parent Aponta Issue ID do Arquivo, Não a Chave
type: trap
tags: [jira, csv, import, epic, initiative, hierarchy, atlassian]
created: 2026-10-05
provenance: residencia_cariri_projects
seen_in: [residencia_cariri_projects]
verified: 2026-10-05 via documentação Atlassian; 2026-10-14 reproduzido numa importação real (importador do projeto sem Issue ID)
confidence: medium
---

# Importador CSV do JIRA: Parent aponta o Issue ID do arquivo, não a chave

## A armadilha

Para importar uma hierarquia (Initiative > Epic > Story) por CSV no JIRA Cloud, parece
natural preencher `Parent` com a chave do pai (`PROJ-12`). Isso não funciona para itens
criados no **mesmo** arquivo, porque as chaves ainda não existem. Também não dá para
prever a chave: Initiatives e Épicos consomem números antes das Stories.

## Dois importadores, comportamentos diferentes

Verificado em 2026-10-14 numa importação real: o importador CSV **do projeto**
(Import work items, sem admin) **não tem** o campo `Issue ID` / `Work item ID` no
mapeamento. Sem ele, toda Story com `Parent = 1` falha no Validate com
`Issue '…' doesn't have a valid Parent selection`. Só o importador **de sistema**
(engrenagem → System → External system import), que exige admin, tem esse campo.

Saída sem admin: importar em **duas etapas**. Primeiro um CSV só com os Épicos (num projeto
vazio, o k-ésimo vira `PROJ-k`); depois um CSV com as Stories e `Parent` = chave real
(`PROJ-1`). O gerador aceita a chave real como argumento, para o caso de o projeto já ter
itens.

## Como funciona (importador de sistema)

- A coluna **`Issue ID`** recebe um número arbitrário, sequencial **dentro do CSV**.
  **`Parent`** recebe esse número. Mapeie as duas colunas no assistente.
- A linha do pai precisa vir **antes** das linhas dos filhos.
- Labels múltiplos ficam em **colunas `Labels` repetidas**, com o mesmo nome de cabeçalho
  e uma label por coluna.
- O formato de data é declarado no assistente. `yyyy-MM-dd` evita ambiguidade.
- A descrição aceita wiki markup (`h3.`, `*`).
- Se o campo Parent não aparecer no mapeamento, habilite Sub-tasks no site.
- O **Epic Link** foi descontinuado em abr/2024. Hoje tudo usa `Parent`.

## Limites que mudam o desenho

- Um nível **acima do épico** (Initiative) exige Premium ou Enterprise, num projeto
  company-managed. A hierarquia é configurada pelo admin e vale **para o site inteiro**.
  Confirme a existência do nível antes de gerar o CSV, e tenha um fallback:
  Épico = projeto e agrupamento = Component.
- O plano Free tem **10 usuários**, o que inviabiliza uma turma inteira.
- O importador nativo do Trello cria um projeto Kanban por board e **não cria épicos**.
- A API REST em lote (`POST /rest/api/3/issue/bulk`) aceita no máximo 50 itens por
  chamada. A descrição precisa estar em ADF.
- **Reimportar duplica.** Depois da primeira importação, o JIRA vira a fonte da verdade.
  Não rode o CSV de novo no mesmo projeto.

## Como aplicar

Gere o CSV por script e valide antes de subir: todo `Parent` existe numa linha anterior,
nenhuma Story fica sem pai e a contagem bate com a fonte. Importe primeiro **um** projeto
de teste e confira a hierarquia antes de importar o resto.

Relacionado: [[Backlog Markdown como Fonte e CSV como Ponte para o JIRA]].
