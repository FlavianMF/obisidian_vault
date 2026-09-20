---
title: Design System Documentado Depois do Build, Não Antes
type: trap
tags: [design-system, documentation, agentic-ai, frontend, armadilha]
created: 2026-09-20
provenance: impeccable
---

# Design System Documentado Depois do Build, Não Antes

**Num mundo visual novo, escrever o `DESIGN.md` antes de construir produz um documento que
passa a ser defendido em vez de descrever.** A regra de [[Impeccable]] é explícita: em
mundo novo ou substituído, o `DESIGN.md` nasce **no finish**, a partir do que foi
construído, escrito pelo subagente documenter. Projeto que já tem identidade coerente é o
caso oposto — aí `/impeccable document` extrai o documento do código existente.

## A armadilha

Um rulebook escrito antes do build falha de duas maneiras ao mesmo tempo:

1. **Vira coisa a defender.** A cada decisão que a realidade da implementação obriga a
   mudar, existe um documento anterior dizendo o contrário — e o reflexo é conformar o
   build ao papel, não corrigir o papel. Decisões que só fazem sentido no abstrato
   sobrevivem porque estão escritas.
2. **Entrega ao detector de design system um alvo instável.** As regras
   `font-outside-DESIGN.md`, `color-outside-DESIGN.md`, `radius-outside-DESIGN.md` e
   `font-size-outside-DESIGN.md` comparam o código contra o documento. Se o documento
   ainda é hipótese, o detector dispara em cima de escolhas legítimas e o ruído treina o
   desenvolvedor a ignorá-lo. Um piso de qualidade que gera falso positivo em massa deixa
   de ser piso — ver [[Detector Determinístico Fora do LLM como Piso de Qualidade]].

O contraponto que confunde: **a ausência de `DESIGN.md` não torna o projeto greenfield.**
Identidade visual coerente já presente no código continua sendo autoridade; o que falta é
o documento, não o mundo. Inventar um mundo novo porque "não achei o `DESIGN.md`" é o erro
simétrico, e mais caro.

## Como detectar

- O `DESIGN.md` foi commitado **antes** do primeiro componente real da superfície nova.
- Ele contém valores que nenhum arquivo do projeto usa (tokens aspiracionais).
- O detector acusa drift de design system em código recém-escrito e a correção que se faz
  é sempre no código, nunca no documento.
- `/impeccable doctor` reporta drift entre os artefatos e o que a versão atual lê.

## O que fazer

- Em mundo visual novo: decidir a direção num artefato **de desenvolvimento** e curto — o
  [[Contrato de Direção Antes do Código]] — e deixar o `DESIGN.md` para o finish. Um mundo
  novo entregue **sem** `DESIGN.md` também é run incompleto; o ponto é a ordem, não a
  dispensa.
- Em projeto existente: `/impeccable document` primeiro, e tratar o resultado como registro
  do que já é verdade, não como aspiração.
- Extensão comum de superfície não reescreve o `DESIGN.md`. Só mudança durável de sistema,
  aprovada, mexe nele.
- Revisar o documento periodicamente para que **um acidente não vire regra** — foi exatamente
  o que aconteceu se um valor entrou lá sem ninguém ter decidido por ele.
- Carimbar quando foi verificado. Documento que afirma estado sem data é
  [[Documentação Desatualizada é Bug, Não Dívida]]; a data de verificação é o mesmo
  instrumento de [[Proveniência como Dado de Primeira Classe]].

## Conexões

O par com [[Slop de IA é Convergência de Treino, Não Falta de Gosto]] é direto: um
`DESIGN.md` escrito antes tende a registrar o default da categoria, porque é o que se tem
em mãos quando ainda não se construiu nada. Ver também
[[Migrar Vários Documentos para um Design System Preservando Nomes de Token e Classe]].
