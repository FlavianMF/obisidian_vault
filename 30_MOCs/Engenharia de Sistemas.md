---
title: Engenharia de Sistemas (MOC)
type: moc
tags: []
created: 2026-05-21
provenance: manual
---

# Engenharia de Sistemas (MOC)

## 📌 Visão Geral
Mapa central para estudos de engenharia de sistemas, focado em processos, MBSE e padrões aeroespaciais.

## 📚 Fontes e Referências
- [[NASA Systems Engineering Handbook|NASA SE Handbook (SP-2016-6105)]]
- [[NASA SE Engine|O Motor de SE da NASA (17 Processos)]]
- [[Fonte_Engenharia_Sistemas|Notas de Estudo Iniciais]]

## 🧠 Conceitos Principais
```dataview
LIST FROM "20_Permanent_Notes"
WHERE type = "concept" OR type = "pattern"
SORT file.name ASC
```

## 🛠️ Ferramentas de Estudo (Utilities)
- [[Cheat Sheet - SE Life Cycle|Mapa Visual: Ciclo de Vida SE]]
- [[90_Assets/Template_Referencia|Template de Referência Bibliográfica]]

## 🚀 Pesquisa e Escrita Acadêmica
- [[Escrita Acadêmica de Alto Impacto]] (Mestre de Escrita)
- [[Estrutura de Artigos Científicos (IMRaD)]]
- [[Apresentação de Modelos MBSE em Artigos]]
- [[Reproduzibilidade e Open Science (2025)]]
- [[Visualização Científica e Resumos Gráficos]]
- [[Estratégia de Publicação e Ética Científica]]

## 🚀 Projetos Ativos
- [[birthday_counter|Birthday Counter (Birthday Counter Experience)]]
```dataview
TABLE status as Status, created as Criado
FROM "20_Permanent_Notes" OR "40_Projects"
WHERE type = "project"
SORT status DESC
```

## 🛠️ Ferramentas e Padrões
- [[Ruby-Testing-Docker|Padrão: Testes Ruby on Rails com Docker]]
- [[Plano de Gerenciamento de Engenharia de Sistemas (SEMP)|O SEMP como Guia de Gestão Técnica]]
```dataview
TABLE type as Tipo, project as Projeto
FROM "20_Permanent_Notes"
WHERE type = "decision" OR type = "pattern" OR type = "trap"
SORT type ASC
```

## 🛠️ Competências e Interesses Técnicos
- [[Flavian Fernandes|Perfil do Pesquisador]]
- [[Sistemas Embarcados]] & Firmware
- [[Sistemas de Controle]] (PID e Controle Moderno)
- [[IoT]] & Edge AI
