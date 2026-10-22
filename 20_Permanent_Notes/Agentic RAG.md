---
title: Agentic RAG
type: concept
tags: [rag, agentic-rag, retrieval, agentic-ai, second-brain]
created: 2026-10-22
provenance: obsidian_vault
verified: 2026-10-22 via pesquisa web com 22 fontes abertas (abstracts e páginas)
confidence: low
seen_in: [obsidian_vault]
---

# Agentic RAG

**Agentic RAG é o RAG em que um LLM controla o fluxo da recuperação: ele decide se busca, onde busca, com que query e se o resultado basta.** No RAG clássico, o desenvolvedor fixa o fluxo. No agentic RAG, a recuperação vira um loop de decisão.

## Do pipeline ao loop

O RAG clássico tem três paradigmas ([[Gao et al 2023 - Survey de RAG]]):

- **Naive RAG**: indexa, recupera o top-k e gera, numa passada só.
- **Advanced RAG**: acrescenta etapas fixas antes e depois da busca (reescrita, busca híbrida, reranking).
- **Modular RAG**: recombina essas etapas como módulos.

Nos três, o fluxo é fixo. O pipeline busca sempre, uma vez, e não sabe se o resultado presta.

O agentic RAG troca o pipeline por um loop:

```
pergunta → [decidir] precisa buscar? ──não──► responde
                │sim
                ▼
           [planejar] reescreve ou decompõe; escolhe a fonte
                ▼
           [buscar] chama a ferramenta (grep, BM25, vetor, web)
                ▼
           [julgar] relevante? suficiente? ──não──► reformula e volta (com teto)
                │sim
                ▼
           [responder] cita as fontes; opcional: escreve de volta na memória
```

A diferença central: **o julgamento sai de um limiar numérico e vai para o modelo**, que lê o candidato antes de usar.

## As quatro capacidades

1. **Roteamento.** O agente escolhe a fonte ou a ferramenta. Ver [[Jeong et al 2024 - Adaptive-RAG]], que escolhe entre sem retrieval, um passo e iterativo pela complexidade da pergunta.
2. **Planejamento.** O agente decompõe a pergunta em subqueries. Ver [[Trivedi et al 2022 - IRCoT]] e [[Yao et al 2022 - ReAct]].
3. **Reflexão.** O agente avalia a relevância e a suficiência e tenta de novo. Ver [[Asai et al 2023 - Self-RAG]] e [[Yan et al 2024 - CRAG]].
4. **Memória.** O agente mantém estado entre passos e sessões. Ver [[Packer et al 2023 - MemGPT]] e [[Xu et al 2025 - A-MEM]].

Taxonomias completas: [[Singh et al 2025 - Survey de Agentic RAG]] e [[Mishra et al 2026 - SoK de Agentic RAG]].

## Padrões

| Padrão | Ideia | Fonte |
|---|---|---|
| Query routing | Escolher a base ou a ferramenta | [[Weaviate 2024 - What is Agentic RAG]], [[IBM - Agentic RAG]] |
| Query rewriting | Reformular quando a busca falha | [[LangChain - Agentic RAG com LangGraph]] |
| Multi-hop iterativo | Alternar raciocínio e busca | [[Trivedi et al 2022 - IRCoT]] |
| Recuperação ativa | Buscar quando a confiança cai | [[Jiang et al 2023 - FLARE]], [[Li et al 2025 - Search-o1]] |
| Avaliador corretivo | Classificar a busca e corrigir | [[Yan et al 2024 - CRAG]] |
| Busca aprendida por RL | Treinar o modelo para buscar | [[Jin et al 2025 - Search-R1]] |
| Orquestrador e workers | Lead planeja, subagentes buscam | [[Anthropic 2025b - Multi-Agent Research System]] |
| Grafo de comunidades | Responder perguntas globais | [[Edge et al 2024 - GraphRAG]] |
| Agentic search sem vetor | grep, glob e Read just-in-time | [[Anthropic 2025a - Effective Context Engineering]], [[Rogut 2026 - RAG is Dead, Right]] |

**Agentic search** é a variante que o Claude Code usa no código: o agente guarda referências leves (paths) e lê o arquivo só quando precisa. RAG não exige vetor. BM25 ou grep também são retrieval, desde que aconteçam durante o raciocínio.

## Implementação mínima

O loop de tool use do próprio LLM já é o agente. Três regras fazem o loop funcionar:

1. **Ferramenta de busca devolve ponteiros, não corpos.** O agente paga tokens só ao abrir um documento.
2. **Teto explícito** de passos e uma saída "a base não cobre isso". Sem teto, o agente busca sem fim ([[Anthropic 2025b - Multi-Agent Research System]]).
3. **Citação obrigatória** de cada fonte usada. A citação torna a resposta verificável.

## Quando não vale

- Pergunta simples, de um salto e uma fonte: um RAG de uma passada ou um grep basta.
- Base com menos de 200 mil tokens: ponha tudo no prompt com cache ([[Anthropic 2024b - Contextual Retrieval]]).
- Tarefa previsível: um workflow fixo é mais barato e mais fácil de depurar ([[Anthropic 2024a - Building Effective Agents]]).
- Latência ou custo apertados: um agente gasta cerca de 4 vezes os tokens de um chat, e um sistema multiagente cerca de 15 vezes.

## Armadilhas

- **Loop e thrash**: busca infinita por algo que não existe.
- **Avaliador fraco**: o próprio agente aprova contexto ruim ou rejeita contexto bom.
- **Erro composto e memory poisoning**: uma nota errada, lida com confiança, contamina a resposta.
- **Avaliação só da resposta final**: esconde falhas da trajetória. Meça também chamadas de ferramenta e tokens por acerto.

## O que NÃO funcionou

Nada foi testado ainda neste vault. A nota resume fontes: os números vêm dos papers e posts, não de medição local. A aplicação ao second brain está em [[Estudo - Agentic RAG no Second Brain]].

## 🔗 Conexões

- [[RFC-001 - Memória de Agentes sobre o Second Brain com Orçamento de Tokens]]
- [[Golden Set para Avaliar Retrieval de Memória do Agente]]
- [[Agentic AI]]
