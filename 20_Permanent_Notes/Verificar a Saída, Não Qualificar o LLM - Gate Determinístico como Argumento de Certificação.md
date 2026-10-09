---
title: Verificar a Saída, Não Qualificar o LLM — Gate Determinístico como Argumento de Certificação
type: concept
tags: [certificacao, do-330, arp4754a, agentic-ai, mbse, assurance, gate]
created: 2026-10-09
provenance: projetos_ita
seen_in: [projetos_ita]
verified: 2026-10-09 via pesquisa web (resumos de fornecedores; texto original das normas não consultado)
confidence: low
---

# Verificar a Saída, Não Qualificar o LLM

## Ideia

Em processo certificado (aeronáutico: ARP4754A para sistemas, DO-178C para software), quem usa uma ferramenta precisa qualificá-la segundo a **DO-330**, a menos que a **saída da ferramenta seja verificada de forma independente**. Ninguém sabe qualificar um LLM. Mas dá para argumentar assim:

> Não qualificamos o LLM. Verificamos tudo o que ele escreve com um validador determinístico independente e medimos quanto erro escapa desse validador.

O **gate determinístico** antes da escrita (propose → validate → commit) deixa de ser só um detalhe de engenharia de agentes. Ele é a **dobradiça da certificação**. A evidência que o argumento exige:
- taxa de escape do gate (escritas válidas mas semanticamente erradas), com intervalo de confiança;
- confiabilidade entre execuções (pass^k, não só pass@1);
- log auditável de proposta, decisão do gate e commit.

## Por que importa

- A EASA ainda não tem posição sobre IA generativa. Ela aparece como "extensão futura", com etapa 2 por volta de Q2/2027, segundo fonte secundária.
- Nenhum trabalho encontrado trata DO-330 aplicada a IA generativa.
- No mercado, fornecedores vendem **acesso** do agente ao modelo. A **evidência** que destrava a adoção em setor certificado continua sem dono.

## Ressalvas

- Normas verificadas só por resumos de fornecedores. Ler o texto original antes de publicar.
- Não está claro como a DO-330 se aplica a ferramentas de nível de sistema sob a ARP4754A.
- Céticos de LLM em assurance cases: https://sos-vo.org/system/files/2025-07/Examining%20Proposed%20Uses%20of%20LLMs%20to%20Produce%20or%20Assess%20Assurance%20Arguments.pdf

## Conexões

- [[Direcao_Tese_e_Carreira]], paper 3 da tese.
- [[Permission-as-Deferred-Promise para Approval Gates de Agente]]
- [[Benchmark Neutro de Fornecedor via Adaptador MCP]], que fornece a taxa de escape medida.
