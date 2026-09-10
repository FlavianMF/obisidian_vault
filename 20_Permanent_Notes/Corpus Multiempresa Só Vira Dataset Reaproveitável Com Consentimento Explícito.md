---
title: Corpus Multiempresa Só Vira Dataset Reaproveitável Com Consentimento Explícito
type: trap
tags: [data-governance, confidentiality, research-design, multi-case-study, llm-council]
created: 2026-09-10
provenance: residencia_00
---

# ⚠️ Corpus Multiempresa Só Vira Dataset Reaproveitável Com Consentimento Explícito

Projetos que coletam dados de **múltiplas empresas/clientes parceiros no mesmo
protocolo** (mesmo roteiro de entrevista, mesmo metamodelo de modelagem) acabam, sem
planejar, com um corpus comparável entre casos — e a tentação natural é reaproveitar
esse corpus (publicação acadêmica, dataset de treino de IA, benchmark interno).
**Nenhum dos 5 conselheiros de um `llm-council` rodado especificamente para avaliar
o desenho desse projeto tocou nisso** — o gap só apareceu na revisão por pares (3 de
5 revisões independentes), quando uma das personas propôs usar os modelos como
"dataset de treino de IA" sem checar se isso era coberto pelo que cada empresa
autorizou.

## Por que passa despercebido

O time projeta a instrumentação técnica da coleta (roteiro, template, matriz V&V —
ver [[Project Model Canvas vs ARCADIA - Mapeamento]]) com cuidado, mas trata
consentimento como assunto de contrato/jurídico, resolvido em algum lugar por outra
pessoa — não como item do protocolo de pesquisa. O uso agregado do dado (reuso como
corpus, não só a entrega individual à empresa que o gerou) é uma decisão posterior à
coleta, então nunca aparece na lista de riscos do desenho original.

## A correção

Tratar consentimento/confidencialidade como **item de protocolo, não opcional**,
antes de considerar qualquer conjunto de casos como corpus reaproveitável:

- Perguntar explicitamente a cada empresa/cliente, antes da coleta, se dados do
  levantamento (modelos, transcrições, entrevistas) podem ser reutilizados além da
  entrega individual — e para quê especificamente (publicação anonimizada? dataset
  de treino? benchmark interno?).
- Não inferir esse consentimento do contrato geral do projeto/programa — é um
  eixo separado, ortogonal ao "vamos entregar uma solução para vocês".
- Se a intenção de reuso agregado não estava clara no momento da coleta, tratar o
  corpus como **não reaproveitável** até obter consentimento retroativo explícito —
  não assumir que o silêncio equivale a autorização.

## 🔗 Conexões
- [[Project Model Canvas vs ARCADIA - Mapeamento]]
- [[Sem Log de Atribuição Por Trilha, Desenho Paralelo Não Prova Eficácia Causal]]
