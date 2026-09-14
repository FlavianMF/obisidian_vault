---
title: PRD — Documento de Requisitos de Produto
type: pattern
tags: [prd, requirements, product, systems-engineering, project-methodology, scope]
created: 2026-09-11
provenance: orbita-platform
project: orbita-platform
---

# PRD — Documento de Requisitos de Produto

> **Nome de arquivo fora da convenção, de propósito.** O vault nomeia notas com frase
> descritiva completa; esta se chama `PRD.md` porque o Obsidian resolve `[[wikilink]]` por
> nome de arquivo, e `[[PRD]]` já era citado por [[Engenharia de Sistemas Agêntica]],
> [[Matriz de V&V - Birthday Counter]] e pelo `00_META/Agent-Instruction.md` desde 2026-05,
> apontando para um stub vazio na raiz. Renomear quebraria os cinco links; o stub foi
> removido e o conteúdo passou a morar aqui.

O PRD é o artefato da **[[Fase A - Desenvolvimento de Conceito]]** do ciclo de vida SE
([[Aplicação das Fases SE em Software Agêntico]]): responde *o que* o sistema faz e *para
quem*, antes de qualquer decisão de *como*. Decisão de como é RFC — ver
[[RFC de Produto - Anatomia e Ciclo de Status]].

## Duas camadas, não uma

A prática madura do `orbita-platform` separa o PRD em dois documentos, e a separação vale a
pena assim que o projeto passa de uma entrega (nível 2+ da
[[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]]):

**Camada 1 — escopo do sistema** (`docs/escopo/Definicoes-Escopo.md`). O sistema inteiro,
incluindo o que ainda não vai ser construído:
- Entidades principais, cada uma tagueada com a fase que a entrega — `Cliente [MVP]`,
  `Consultor de Investimentos [Fase 2]`, `Banco/Corretora [Fase 2/3]`.
- Relações entre entidades.
- Casos de uso `UC1..UCn`, também tagueados por fase.
- Áreas de análise operacional: integrações externas, compliance e segurança, monetização.

Esta camada quase não muda. É ela que impede a Fase 2 redescobrir do zero um ator que a
Fase 1 já tinha previsto.

**Camada 2 — especificação da release** (`docs/escopo/MVP-Especificacao.md`). O recorte
desta entrega:
- **Em escopo × fora de escopo**, lado a lado, em listas explícitas. Sem essa seção, o
  escopo cresce por omissão.
- Atividades operacionais prioritárias `ACT-*`, ligadas aos `UC*` da camada 1.
- Modelo de dados simplificado da release.
- Arquitetura técnica e orquestração de infraestrutura.

Em projeto de nível 1 (script/ferramenta) as duas camadas colapsam numa página só:
problema, dentro/fora, critério de aceite. Nada mais.

## Requisito que serve de aceite

Requisito que não dá para reprovar não é requisito. A forma que funciona é
`[Ator] + [Verbo] + [Objeto] + [Restrição]` (ver
[[Processo de Definição Pré-Desenvolvimento (Elite SE Workflow)]]), e o teste da frase é:
*consigo escrever um teste automatizado que falha se isto não valer?* Requisito de segurança
e de isolamento entre tenants vira **teste negativo** — "o consultor **não** vê cliente com
vínculo revogado" — porque é a forma que pega a regressão.

A ponte requisito → prova é a matriz de V&V ([[Matriz de V&V - Birthday Counter]]): cada
requisito recebe um método de verificação, e a matriz é reaberta sempre que o PRD muda.

## O que NÃO entra no PRD

- **Decisão de arquitetura.** Vai para uma RFC, com a alternativa rejeitada registrada.
- **Sequenciamento de entrega.** Vai para o plano de fase
  ([[Plano de Fase em Etapas Mescláveis]]).
- **Armadilha de implementação.** Vai para o playbook
  ([[Playbook de Projeto - Erros Já Cometidos Como Artefato]]).

Misturar as quatro coisas num documento só é o modo mais rápido de nenhuma delas ficar
atualizada — e nota desatualizada é bug, não dívida
([[Documentação Desatualizada é Bug, Não Dívida]]).

## Ciclo de vida

O PRD nasce do **documento de intenção do usuário** — prosa crua, versionada como veio, sem
edição. Antes de transcrevê-lo em requisito, o agente **faz perguntas de curadoria**: no
`orbita-platform` o próprio texto de origem terminava com "me faça perguntas para definir
melhor as RFCs". Adivinhar ali custa uma fase inteira.

Depois disso o PRD é **estável e citável**: mudança de escopo entra como decisão numerada no
RFC-000 da fase, não como edição silenciosa no PRD.

## 🔗 Conexões
- [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]]
- [[RFC de Produto - Anatomia e Ciclo de Status]]
- [[Plano de Fase em Etapas Mescláveis]]
- [[Fase A - Desenvolvimento de Conceito]]
- [[Aplicação das Fases SE em Software Agêntico]]
- [[Processo de Definição Pré-Desenvolvimento (Elite SE Workflow)]]
- [[Matriz de V&V - Birthday Counter]]
- [[Engenharia de Sistemas Agêntica]]
