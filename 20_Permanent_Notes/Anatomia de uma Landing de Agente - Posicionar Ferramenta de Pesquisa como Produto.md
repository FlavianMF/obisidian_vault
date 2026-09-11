---
title: Anatomia de uma Landing de Agente — Posicionar Ferramenta de Pesquisa como Produto
type: pattern
tags: [product, positioning, marketing, agentic-ai, research-to-product, mbse]
created: 2026-09-11
provenance: projetos_ita
project: projetos_ita
---

# Anatomia de uma Landing de Agente — Posicionar Ferramenta de Pesquisa como Produto

## Contexto

Para transformar uma ferramenta de pesquisa (agente de IA que opera modelos
Capella/MBSE) numa apresentação de produto, o material de referência foi o
[MecAgent](https://mecagent.com) — um agente que opera softwares de CAD mecânico.
Mesmo intuito, domínio vizinho, e três anos à frente em maturidade comercial
(US$ 3 mi levantados, tiers públicos de US$ 84 a US$ 417/mês).

## Padrão

A estrutura que se repete em landing de agente que opera ferramenta estabelecida:

1. **Claim de uma linha, nomeando categoria + domínio.** *"The First AI CAD Copilot
   for Mechanical CAD Software"*. Não é slogan abstrato: diz o que é e onde roda.
2. **Copiloto, não substituto.** Camada sobre ferramenta que o time já usa, sem
   retreinar ninguém. Reduz a objeção de adoção antes que ela seja levantada.
3. **Features com nome de produto**, não de função: *Specs-to-CAD*, *Compliance
   check*, *Live pricing* — em vez de "conversão de texto para modelo".
4. **Lista de integrações como prova de alcance** (SolidWorks, CATIA, Creo…). O
   equivalente num agente MBSE são as camadas/formatos cobertos.
5. **Publicar os limites.** O MecAgent divulga benchmarks *e* onde o agente falha
   ("limited" para superfícies avançadas e geometria com raciocínio espacial forte).
   Contraintuitivamente, isso **constrói** credibilidade — e é o item que a maioria
   dos pitches de pesquisa omite.
6. **Tiers públicos**, mesmo que aspiracionais.
7. **Precedente em domínio vizinho** como prova de que a tese funciona.

## Adaptação para público acadêmico

Apresentando ao orientador, duas inversões em relação a uma landing comercial:

- **O slide de negócio termina em pergunta, não em CTA.** Quando existe decisão
  pendente com terceiros (no caso: parecer de conselho, conversa com o NIT do ITA,
  licença ainda indefinida), enquadrar como "isto é o que poderia ser, e é o que
  preciso decidir com você" — não como plano fechado.
- **Cada número carrega a fonte.** Latência veio do export de sessão; contagem de
  ferramentas de `grep -c "@mcp.tool()"`; custo de erro tardio de Ulrich & Pearson e
  do INCOSE Handbook. Onde a fonte era frágil (o multiplicador "10× por fase",
  popular mas não rastreável aos dados originais), usar a direção do argumento sem se
  comprometer com o número.

## Quando aplicar

Ao converter qualquer protótipo de pesquisa em material de apresentação para público
que decide (investidor, orientador, banca, patrocinador interno). Pesquisar um
concorrente/análogo do domínio vizinho antes de escrever o primeiro slide é o passo
que mais economiza tempo — a estrutura já existe pronta, resta preencher.

## 🔗 Conexões
- [[Apresentação de Modelos MBSE em Artigos]]
- [[Notas de Análise Envelhecem em Dias - Reverificar no Código Antes de Apresentar]]
