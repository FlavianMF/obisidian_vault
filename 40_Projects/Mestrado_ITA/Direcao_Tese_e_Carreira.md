---
title: Direção da Tese e da Carreira — Consultoria Primeiro, Pesquisa como Credencial
type: project
tags: [mestrado, carreira, consultoria, mbse, agentic-ai, certificacao, capella]
created: 2026-10-09
provenance: projetos_ita
project: projetos_ita
verified: 2026-10-09 via conversa com o usuário + notas em projetos_ita/notes/
confidence: medium
---

# Direção da Tese e da Carreira

Origem: [[Proposta_Pesquisa_MBSE_AI]] (mai/2026) e [[Palestra_SE_Business]] (mai/2026). Esta nota registra a virada de out/2026.

## Objetivo de carreira (declarado em 2026-10-09)

**Consultoria primeiro.** O caminho é trabalhar com grandes empresas, fazer parcerias, dar palestras e cursos. O produto (stack `capella_mcp` + `capella_llm_window`, ou uma camada de verificação) fica em segundo plano, como acelerador das consultorias, e não como trabalho em tempo integral.

A ideia já vinha aparecendo antes:
- **mai/2026:** a [[Palestra_SE_Business]] traduz o método NASA para negócio.
- **ago/2026:** os councils de monetização de 26 e 27/08, em `projetos_ita/notes/council/`, adiaram a consultoria para 2027 por falta de tempo.

Em out/2026 a consultoria virou **o objetivo**, e não mais uma frente paralela. Por isso a pesquisa passa a ser escolhida pelo quanto alimenta a consultoria: credibilidade, visibilidade e rede de contatos.

## Cenário competitivo (out/2026)

- **Obeo "AI for Capella":** add-on comercial lançado no fim de julho de 2026. Expõe o Capella a agentes externos via MCP, mas não tem chat próprio. O preço é sob cotação. O usuário pediu trial e aguarda resposta.
- **DigitalThread.ai "Capella Agent":** palestra no Capella Days de 03/12/2026. Alega mais de 100 tools, BYOK, Ollama, undo e audit log. Conhecido só pelo abstract.
- **AMIGO (KIT, MODELS 2026):** MCP com validador para o Palladio. Mostra que um gate antes da escrita já é básico, e não novidade de doutorado.
- **ISAE-SUPAERO (Ober et al.):** 4 protótipos de LLM no Capella, incluindo MCP. É o baseline acadêmico direto. O trabalho futuro deles é agentes cientes da metodologia e escala de tools.
- **Conclusão (council v4):** competir com a Obeo no produto é ilusão. A Obeo vende **acesso**; ninguém vende **evidência de confiança**.

## Espinha da tese: 3 papers "base"

1. Benchmark aberto e neutro de fornecedor, com pass^k (**MERIT**, Model Edit Reliability In Tools). É o motor de citação e a vitrine da consultoria. Ver [[Benchmark Neutro de Fornecedor via Adaptador MCP]].
2. Oráculos semânticos: "quando a validação estrutural mente".
3. Argumento de garantia sob DO-330/ARP4754A. Ver [[Verificar a Saída, Não Qualificar o LLM - Gate Determinístico como Argumento de Certificação]].

Hipóteses H1–H8, kit da tese e roteiro de entrevistas: `projetos_ita/notes/research/hipoteses_doutorado.md` e `projetos_ita/notes/tese/`.

## Ofertas de consultoria que derivam da pesquisa

- Diagnóstico de onde a IA cabe no processo de MBSE de uma empresa.
- Workshop ou curso de IA em engenharia de sistemas com segurança e rastreabilidade.
- Piloto de agente com gate de verificação, medido com o MERIT.
- Apoio para montar evidência de certificação de uso de IA sob ARP4754A.

## Doutorado

Ainda não decidido.
- **A favor:** abre porta em aeroespacial e defesa.
- **Alternativa:** mestrado forte com 2–3 papers, palestras no INCOSE e talvez a certificação CSEP.
- **Meio-termo:** doutorado em parceria com uma empresa.

## Próximos marcos

- **13/10/2026:** evento INCOSE no ITA. Folha de campo em `projetos_ita/notes/tese/folha_evento_incose.html`. Objetivo: 3–5 conversas de validação de mercado.
- **03/12/2026:** Capella Days. Rever as alegações da DigitalThread e da BIG ("Propose, Gate, Commit").
- **15/12/2026:** checkpoint de corte definido no council v4.
- Contato com Ileana Ober (ISAE) para validar a novidade e explorar colaboração.

## Conexões

- [[MBSE com Agentic AI]]
- [[IA Generativa na Engenharia de Sistemas]]
- [[jev-workflow]]: o desenho de seleção de tools da ferramenta E serve de protocolo para a hipótese H4.
- [[Benchmark Sem Baseline Degenerado Não Diz Quanto do Score é Capacidade]]
