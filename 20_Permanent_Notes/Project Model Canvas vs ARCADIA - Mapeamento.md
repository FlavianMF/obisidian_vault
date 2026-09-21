---
title: Project Model Canvas vs ARCADIA — Mapeamento
type: pattern
tags: [mbse, arcadia, project-model-canvas, systems-engineering, product-definition, verification-validation, llm-council, research-design]
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

## 🧭 Pressure-test via llm-council — veredito e correções

Rodar essa abordagem paralela (8 empresas, 4 alunos leigos por empresa, 1 visita de
campo) por um conselho de 5 personas de IA + revisão por pares (skill
`llm-council`) confirmou "eficaz com ressalvas" — nenhuma persona recomendou contra
— mas convergiu em risco operacional real: carga alta (13 blocos PMC + OA/SA + V&V
num único dia) com equipe sem treino prévio degrada silenciosamente antes de quebrar
de forma óbvia. Três correções concretas, de baixo custo, condicionam o "eficaz":

1. **Papéis fixos por aluno antes da viagem** — 1 conduz, 1 anota PMC, 1 anota
   ARCADIA/OA, 1 cronometra e sinaliza divergência. Sem isso a checagem cruzada
   proposital (ver acima) vira bagunça — ninguém captura os dois lados ao mesmo
   tempo.
2. **Dry-run obrigatório** — role-play com uma "empresa" fictícia usando o roteiro
   real, injetando uma contradição PMC/ARCADIA deliberada, antes da primeira visita
   de verdade. Calibra "divergência real" vs. ambiguidade normal de linguagem — sem
   isso, um novato não distingue as duas coisas na hora.
3. **Reformular a alegação de pesquisa** — ver [[Sem Log de Atribuição Por Trilha, Desenho Paralelo Não Prova Eficácia Causal]].

Ver também o blind spot de governança de dados capturado só na revisão por pares:
[[Corpus Multiempresa Só Vira Dataset Reaproveitável Com Consentimento Explícito]].

## 📋 Compartilhar o preenchimento do PM Canvas com os alunos (FigJam)

Lacuna real até 2026-09-21: a metodologia acima definia **o quê** preencher (13
blocos) mas não **como** os 4 alunos por empresa preenchiam isso juntos, ao vivo,
sem treino prévio em nenhuma ferramenta nova. Resolvido criando um **template
mestre num board FigJam colaborativo** (via Figma MCP) — grid visual dos 13
blocos/5 colunas, tint de cor por coluna, cada bloco com a pergunta-guia já
extraída do roteiro de entrevista (não uma pergunta nova), mais uma seção "Como
usar" fixa no próprio board.

Decisões que valem para qualquer residência multiempresa parecida:

- **Um template mestre, nunca um board único com as N empresas juntas** —
  duplicar por empresa antes de preencher, e compartilhar a cópia só com o
  time+mentores daquela empresa. Aplica direto a
  [[Corpus Multiempresa Só Vira Dataset Reaproveitável Com Consentimento Explícito]]:
  a fronteira de confidencialidade é por cópia do artefato, não um acordo geral do
  programa.
- **Canvas colaborativo (FigJam/Miro), não markdown estático, quando o
  preenchimento acontece ao vivo em campo por várias pessoas ao mesmo tempo** — o
  padrão markdown-no-repo (usado pro `template_visita_arcadia.md`) funciona bem
  pra formulário linear preenchido por 1 pessoa; um canvas de 13 blocos
  preenchido simultaneamente por 4 alunos pede um board de verdade.
  Digitalização continua acontecendo depois: o conteúdo final é transcrito pro
  markdown do repo como registro permanente em git — o board é a superfície de
  trabalho ao vivo, não o arquivo de sistema de registro.
- **Perguntas-guia em cada bloco vêm do roteiro de entrevista já validado**, não
  de uma reformulação nova do framework — reduz a chance de o board virar uma
  segunda fonte de verdade divergente do processo de entrevista.

## 🔗 Conexões
- [[Capella no Processo de Definição de Produto]]
- [[Processo de Definição Pré-Desenvolvimento (Elite SE Workflow)]]
- [[MBSE]]
- [[Plano de Gerenciamento de Engenharia de Sistemas (SEMP)]]
- [[V-Model (Vee Model)]]
- [[Matriz de V&V - Birthday Counter]]
- [[Sem Log de Atribuição Por Trilha, Desenho Paralelo Não Prova Eficácia Causal]]
- [[Corpus Multiempresa Só Vira Dataset Reaproveitável Com Consentimento Explícito]]
