---
title: Backlog Markdown como Fonte e CSV como Ponte para o JIRA
type: pattern
tags: [jira, csv, backlog, markdown, project-management, automation, scrum]
created: 2026-10-05
provenance: residencia_cariri_projects
seen_in: [residencia_cariri_projects]
verified: 2026-10-05 via _tools/jira-csv/gerar_csv.py (8 CSVs, 336 Stories, checagens passando)
confidence: medium
---

# Backlog em markdown como fonte, CSV como ponte para o JIRA

## O padrão

Quando o backlog nasce em markdown versionado (canvas → backlog por projeto), não
cadastre item por item na ferramenta nem use importador de outra ferramenta. Escreva um
**script stdlib** que lê os `.md` e gera **um CSV de importação por projeto**, com a
hierarquia já montada. O markdown fica como registro da versão inicial. Depois da
importação, o JIRA passa a ser a fonte da verdade.

Caso real (Residência Cariri, 8 empresas): `_tools/jira-csv/gerar_csv.py` monta
Initiative (projeto Pk) > Épico (Grupo de entregas) > Story (item do backlog), com 336
Stories em 8 CSVs, a partir de backlogs pensados para o Trello.

## Regras que funcionaram

- **A hierarquia vem da estrutura do documento, não do número do ID.** O épico é a seção
  `## <Nome> — label \`slug\``. Havia IDs fora de ordem (`IBK-38` dentro de `validacao`).
- **Título do bloco de lista + detalhe do `###`.** O bloco de código "colar na lista" dá
  o título de cada item. O `###` dá o prazo, o critério de aceite e a checklist. Faixas
  como `### X-30 a X-33` viram N Stories, cada uma com a sua data
  (`semana 1 → 27/11 · …`).
- **A faixa de prioridade decide a profundidade.** Foco ganha Initiative, Épicos e
  Stories. Bônus ganha Initiative e Épicos, sem Stories. Próxima fase ganha só a
  Initiative. Isso evita detalhar o que não vai ser feito.
- **O ID antigo sai do título** e vai para uma linha "Origem" na descrição. A chave nova
  do JIRA é que vai para branch e commit, por causa da integração com o Bitbucket.
- **Subpassos viram checklist na descrição**, não Subtask. Itens de 0,5 a 2 dias não
  precisam de outro nível, e 1.000 subtasks poluem o board.
- **Checagens que param o script:** o Parent existe e vem antes, nenhuma Story fica sem
  pai, a contagem de Stories bate com os IDs distintos do backlog.
- **Flag de fallback** (`--sem-initiative`) para quando o site não tem o nível acima do
  épico. A saída vai para outra pasta, para não sobrescrever o CSV principal.

## Por que não o importador do Trello

O importador nativo cria um projeto Kanban por board e não cria épicos. A hierarquia,
que é o objetivo da migração, se perde.

Armadilhas do formato: [[Importador CSV do JIRA - Parent Aponta Issue ID do Arquivo, Não a Chave]].
Decisões de método: [[Scrum Enxuto para Residência com Alunos em Tempo Parcial]].
