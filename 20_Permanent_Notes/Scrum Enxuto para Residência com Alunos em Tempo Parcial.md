---
title: Scrum Enxuto para Residência com Alunos em Tempo Parcial
type: decision
tags: [scrum, jira, project-management, residencia, students, agile, methodology]
created: 2026-10-05
provenance: residencia_cariri_projects
seen_in: [residencia_cariri_projects]
verified: 2026-10-05 via grill com o coordenador; Scrum Guide 2020
confidence: low
---

# Scrum enxuto para residência com alunos em tempo parcial

Contexto: programa de 3 meses com prazo fixo, 8 empresas parceiras, 4 alunos por
empresa (4 h/dia, 5 dias/semana) e 2 coordenadores. A primeira escolha foi Trello Kanban
(o Jira parecia "pesado demais"). Ela foi revertida antes de qualquer board existir,
quando apareceu o **JIRA Enterprise da instituição**. O motivo real da escolha anterior
era custo e limite de usuários, não peso.

## Decisões

- **Hierarquia:** Initiative = projeto priorizado da empresa (P1, P2…). Épico = Grupo de
  entregas do canvas. Story = entrega de 0,5 a 2 dias. Prioridade e faixa (`foco`,
  `bonus`, `proxima-fase`) viram labels.
- **Um projeto company-managed por empresa** com esquema compartilhado. Isso isola
  permissões e mantém boards e JQL iguais. A visão do programa fica em boards por filtro
  e no Plans.
- **O coordenador é PO e SM leve ao mesmo tempo.** A empresa raramente tem tempo de
  ordenar backlog, e os alunos precisam de alguém que cobre. A empresa entra como
  stakeholder num **refinamento quinzenal**.
- **Sprint de 2 semanas, todas sincronizadas.** Uma semana dá pouca capacidade (cerca de
  160 h por sprint para 4 alunos). Quatro semanas dão pouco feedback.
- **Daily assíncrona por texto no canal que já existe** (o grupo de WhatsApp da
  empresa), no formato ontem/hoje/bloqueio. O bloqueio também vira Flag no JIRA. Review e
  retro somam cerca de 35 min no último dia.
- **Story points 1/2/3.** Acima de 3, a Story deve ser quebrada. A velocity serve só para
  o próprio grupo e nunca para comparar grupos ou avaliar alunos.
- **Os títulos migrados ficam como estão** (verbo + objeto). O formato "Como… quero…" vale
  só para Stories novas, porque reescrever 300 itens custa mais do que rende.
- **Só o PO move para Concluído.** Há uma DoD única para o programa: critério de aceite
  atendido + evidência linkada (PR ou arquivo) + revisão.
- **Semana 1 fora da ferramenta.** O Sprint 1 começa quando o backlog está carregado.

## O que reverter se der errado

Se a daily por WhatsApp virar ruído, migrar para comentário na Story. Se o refinamento
quinzenal não acontecer, o PO refina sozinho e a empresa só vê a review.

Ferramenta: [[Backlog Markdown como Fonte e CSV como Ponte para o JIRA]].
Como se chegou aqui: [[Pesquisa Paralela por Agentes Antes do Grill]].
