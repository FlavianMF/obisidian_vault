---
title: Project Model Canvas vs ARCADIA — Mapeamento
type: pattern
tags: [mbse, arcadia, project-model-canvas, systems-engineering, product-definition, verification-validation]
created: 2026-09-03
provenance: residencia_00
---

# 🎯 Project Model Canvas vs ARCADIA — Mapeamento

Quando um projeto de definição de produto usa o **Project Model Canvas** (PM Canvas,
José Finocchio Jr., 13 blocos em 5 colunas: Por quê/O quê/Quem/Como/Quando-Quanto)
como ferramenta de kickoff, e existe intenção de aplicar MBSE, **ARCADIA cobre 9 dos
13 blocos com ganho de rastreabilidade** — mas não substitui os 4 blocos de gestão
de projeto pura. Abordagem validada em campo (residência técnica, 8 empresas): rodar
os dois **em paralelo**, não como substituição — PM Canvas define o **negócio**,
ARCADIA define o **produto**.

## 🗺️ Mapeamento

| Bloco PM Canvas | Equivalente ARCADIA |
| --- | --- |
| Justificativas | OA — dores/lacunas em cenários "As-Is" dos atores |
| Objetivos | OA/SA — Missões e Capabilities rastreáveis |
| Benefícios | OA — valor das Operational Activities/Capabilities (sem bloco formal em ARCADIA) |
| Produto | SA (fronteira do sistema) + PA/EPBS |
| Requisitos | SA — requisitos derivados de Capabilities, rastreados |
| Stakeholders Externos | OA — Operational Actors/Entities (OEB) |
| Premissas | OA/SA — assumptions vinculadas ao elemento dependente |
| Restrições | SA/LA — constraints/não-funcionais; condições ambientais já na OA |
| Riscos | LA — trade-off studies entre arquiteturas alternativas (parcial: risco de projeto continua sendo gestão) |

**Fora do escopo do ARCADIA** (continuam sendo blocos de gestão, não descartar):
Equipe, Grupos de Entregas, Linha do Tempo, Custos. Os gates OA→SA→LA→PA dão marcos
naturais para ancorar um cronograma, mas não o substituem.

## 💡 Quando vale rodar os dois em paralelo (não substituir)

- Múltiplos times/empresas em paralelo precisando de estrutura comparável entre si
  (mesmo metamodelo ARCADIA > canvas heterogêneo por time).
- Produto evolui ao longo do projeto e precisa de rastreabilidade
  necessidade→requisito→função→componente, que o Canvas (documento estático) não tem.
- Equipe tem tempo/mentoria para ao menos Operational Analysis + System Analysis.

Os blocos onde os dois se sobrepõem (Justificativas, Objetivos, Stakeholders
Externos, Restrições) não são redundância — servem de **checagem cruzada
proposital**: se o "Objetivo" do PM Canvas (linguagem de negócio) não corresponde a
nenhuma Capability modelada em OA (linguagem operacional), é sinal de alerta
precoce de necessidade mal capturada ou discurso de negócio desalinhado da
realidade.

## ✅ V&V por perspectiva ARCADIA

Critério de aceitação por perspectiva, ancorado em [[V-Model (Vee Model)]]
(verificação = "build the system right", validação = "build the right system"):

| Perspectiva | Tipo | Critério |
| --- | --- | --- |
| OA | Validação | Cenário operacional bate com a realidade confirmada pelo stakeholder |
| SA | Verificação | Requisitos completos/consistentes/testáveis, rastreados a uma Capability |
| LA | Verificação | Trade-off explícito documentado, não escolha arbitrária |
| PA | Verificação | Componente atende à restrição industrial levantada em campo |

Matriz reutilizável adaptada de [[Matriz de V&V - Birthday Counter]] (ID, Descrição,
Tipo Ver./Val., Perspectiva ARCADIA, Método I/A/D/T, Critério de sucesso
mensurável). Todo VAL-xx referencia a OA de origem; todo RQ-xx referencia a
Capability de origem — sem isso a matriz não fecha rastreabilidade.

Ponto-chave de ARCADIA para V&V: o IVVQ do método é conduzido a partir de
Capabilities/Functional Chains/Cenários do próprio modelo, não de requisitos em
texto solto — o cenário que gera o requisito já serve de roteiro de verificação
(fonte: [ARCADIA Q&A](https://mbse-capella.org/arcadia-qna.html)).

## ⚠️ Adaptação pragmática — "ARCADIA enxuto"

Quando a equipe não tem tempo/treino para Capella completo antes de uma visita de
campo: usar um formulário de papel cobrindo só OA (atores, cenário As-Is/To-Be,
fronteira do sistema, restrições, critérios de sucesso) na visita; transcrever para
Capella depois; LA/PA entram só quando o produto amadurecer. Regra mínima: todo
requisito registrado deve apontar de volta para um ator/dor de origem.

## 🔗 Conexões
- [[Capella no Processo de Definição de Produto]]
- [[Processo de Definição Pré-Desenvolvimento (Elite SE Workflow)]]
- [[MBSE]]
- [[Plano de Gerenciamento de Engenharia de Sistemas (SEMP)]]
- [[V-Model (Vee Model)]]
- [[Matriz de V&V - Birthday Counter]]
