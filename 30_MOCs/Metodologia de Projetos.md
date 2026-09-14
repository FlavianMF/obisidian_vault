---
title: Metodologia de Projetos
type: moc
tags: [moc, project-methodology, prd, rfc, dev-workflow, documentation]
created: 2026-09-11
provenance: orbita-platform
---

# 🗺️ Metodologia de Projetos

Mapa de conteúdo de **como um projeto é definido, sequenciado, construído e encerrado**.
Dois eixos que se completam: *o que construir e em que ordem* (a cadeia de artefatos) e
*como construir* (o workflow de desenvolvimento).

## 🧭 Comece por aqui
- [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]] — a nota-mãe: a cadeia
  completa, os três níveis de aplicação e as convenções de forma.
- [[Checklist de Bootstrap de Workflow de Desenvolvimento]] — os sete eixos de disciplina de
  desenvolvimento (worktree, escopo de teste, relatório de CI, branches, release, introspecção
  de versão, documentação viva).

## 📄 Os artefatos
- [[PRD]] — requisitos e escopo: as duas camadas, requisito que serve de aceite, o que não
  entra.
- [[RFC de Produto - Anatomia e Ciclo de Status]] — decisão técnica, numeração, status vivo,
  alternativa rejeitada.
- [[Plano de Fase em Etapas Mescláveis]] — `E0..En`, dependências, aceite como teste negativo,
  fatiamento sob demanda.
- [[Nota de Conclusão de Etapa é Entregável, Não Relatório]] — rastreabilidade, achados,
  verificação, fora de escopo.
- [[Playbook de Projeto - Erros Já Cometidos Como Artefato]] — o tático que impede repetir
  erro já pago.
- [[Padrão de Documentação Agêntica Local]] — a estrutura mínima de `docs/` em qualquer
  projeto.

**Esqueletos prontos** em `90_Assets/`: `Template_PRD`, `Template_RFC-000-Visao-de-Fase`,
`Template_RFC`, `Template_Plano-de-Fase`, `Template_Nota-de-Etapa`, `Template_Playbook`,
`Template_Prompt-de-Sessao`, `Template_Project_Prompt`.

## 🔬 Fundamento de Engenharia de Sistemas
- [[Ciclo de Vida de Engenharia de Sistemas]] · [[NASA SE Engine]] · [[V-Model (Vee Model)]]
- [[Pré-Fase A - Análise de Conceito]] · [[Fase A - Desenvolvimento de Conceito]] ·
  [[Fase B - Definição Preliminar]] · [[Fase C - Design Final e Fabricação]] ·
  [[Fase D - Montagem, Integração e Teste (AI&T)]] · [[Fase E - Operações e Sustentação]] ·
  [[Fase F - Encerramento (Closeout)]]
- [[Aplicação das Fases SE em Software Agêntico]] — o mapeamento fase → artefato.
- [[Processo de Definição Pré-Desenvolvimento (Elite SE Workflow)]] — requisitos L1, FSM,
  fronteira do sistema.
- [[Plano de Gerenciamento de Engenharia de Sistemas (SEMP)]] · [[Framework 3 Pilares SE]] ·
  [[Análise de Trade-off (Trade Study)]]

## ⚙️ Execução e disciplina
- [[Skill - Fluxo de Trabalho de Feature Branch]] — branch simples × worktree dedicada.
- [[Confirmar Qual Worktree Está Sendo Testada Antes de Diagnosticar]]
- [[Push Pra Branch Ocupada Via Branch Temporária]]
- [[Automação de Release - Tag e Build Têm Que Estar no Mesmo Job]] ·
  [[Tag de Release Não Volta Pra Develop Sozinha]]
- [[Gate de Cobertura Tem Que Excluir do Numerador E do Denominador, Não Só Relaxar o Limiar]]
- [[Escopo de Trigger de CI - push Só nas Branches Protegidas, pull_request Cobre o Resto]]

## 🧠 Documentação viva
- [[Documentação Desatualizada é Bug, Não Dívida]] — o princípio.
- [[Notas de Análise Envelhecem em Dias - Reverificar no Código Antes de Apresentar]] — o lado
  da leitura.
- [[Engenharia de Sistemas Agêntica]] · [[Orquestração Híbrida de Agentes]]
