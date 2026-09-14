---
title: Template_PRD
type: template
tags: [template, prd, requirements, scope]
created: 2026-09-11
provenance: orbita-platform
---

# Template — PRD (`docs/escopo/`)

Esqueleto do [[PRD]]. Em projeto de **nível 3** ele se divide em dois arquivos (escopo do
sistema + especificação da release); em **nível 2** vira um arquivo só; em **nível 1**, as
seções 1 e 4 apenas. Ver [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]].

---

## Arquivo A — `docs/escopo/Definicoes-Escopo.md` (escopo do sistema)

```markdown
# {{title}} — Escopo do Sistema

## Visão Geral
<!-- Duas frases: que problema o sistema resolve, para quem. -->

## Domínio
<!-- O recorte de negócio. O que está dentro do domínio e o que é sistema de terceiro. -->

## Entidades Principais
### 1. <Entidade> `[MVP]`
<!-- Uma entidade por subseção, com a TAG DA FASE que a entrega: [MVP] / [Fase 2] / [Fase 3].
     Inclua entidades que ainda não serão construídas — é o que evita redescobri-las depois. -->

## Relações entre Entidades
<!-- Cardinalidade e a regra que a governa. -->

## Casos de Uso Prioritários
### UC1: <nome> `[MVP]`
<!-- Ator, gatilho, resultado observável. Numerados e tagueados por fase. -->

## Áreas de Análise Operacional
### Integrações Externas
### Compliance e Segurança
### Monetização

## Próximos Passos
## Referências
```

---

## Arquivo B — `docs/escopo/<Release>-Especificacao.md` (a entrega)

```markdown
# Especificação do <MVP | Release N> — {{title}}

## Visão Geral
<!-- Qual proposta de valor esta release valida. -->

## Relação com a Engenharia de Sistemas
<!-- Links: origem do escopo, origem dos dados, análise operacional. -->

## 1. Escopo: Dentro vs. Fora
### 1.1 Em Escopo
### 1.2 Fora de Escopo
<!-- As duas listas, lado a lado, explícitas. Sem esta seção o escopo cresce por omissão. -->

## 2. Atividades Operacionais Prioritárias
<!-- ACT-001…, ligadas aos UC* do arquivo A. -->
### 2.1 Detalhamento de Funcionalidades Especiais

## 3. Modelo de Dados Simplificado
### 3.1 Diagrama de Entidades
### 3.2 Tabelas Necessárias

## 4. Arquitetura Técnica
### 4.1 Orquestração da Infraestrutura

## 5. Próximos Passos
```

## 🔗 Conexões
- [[PRD]]
- [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]]
