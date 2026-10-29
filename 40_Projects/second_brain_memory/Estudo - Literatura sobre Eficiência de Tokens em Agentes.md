---
title: Estudo — Literatura sobre Eficiência de Tokens em Agentes
type: project
tags: [study, literature, tokens, efficient-reasoning, context-pruning, model-routing, agents, coding-agents]
created: 2026-10-26
provenance: obsidian_vault
project: second_brain_memory
confidence: low
scope: project
verified: 2026-10-26
---

# Estudo — Literatura sobre Eficiência de Tokens em Agentes

**Status**: Levantamento fechado em 2026-10-26 · **Data**: 2026-10-26 · Complementa o §3 do [[Estudo - Orquestração de Agentes e Economia de Tokens]], que já cobre FrugalGPT, RouteLLM, AutoMix, LLMLingua, ACON, Complexity Trap, ReWOO, CodeAct, Agentless, AgentPrune e Kim et al.

## 1. Método e ressalvas

- Três agentes Sonnet pesquisaram três eixos em paralelo: raciocínio, contexto e memória, e agentes com consciência de custo.
- Os 36 trabalhos foram lidos **só pelo abstract**. Antes de citar um número numa decisão, abra o texto completo.
- Conferi 3 IDs à mão: 2604.22750, 2609.22951 e 2603.15183. Os números batem com os abstracts.
- Muitos trabalhos são de 2026, com autor único ou relato do próprio autor. Nenhum foi replicado.
- O FastContext (2606.14066) foi retirado pelo autor em 2026-06-30. Ele fica fora da síntese.

## 2. Onde está o custo

| Referência | arXiv | Achado | Consequência |
| --- | --- | --- | --- |
| Bai et al., _How Do AI Agents Spend Your Money?_ | 2604.22750 | Tarefa agentic de código gasta 1000x os tokens de um chat de código. O input domina o custo. A mesma tarefa varia até 30x. A acurácia costuma ter pico num custo intermediário. O modelo prevê o próprio gasto com correlação de no máximo 0,39. | Confirma a M5 local: a releitura do contexto custa mais que a saída. Estimar o custo antes não funciona. Use teto e parada em tempo de execução. |
| Fan et al., SWE-Effi | 2509.09853 | "Token snowball": o agente preso numa tarefa insolúvel queima recursos. | Detecte futilidade. Ponha teto de passos e de tokens por tarefa. |
| Kapoor et al., _AI Agents That Matter_ | 2407.01502 | Pede avaliação conjunta de custo e acurácia. | Reporte a fronteira de Pareto, não só a acurácia. |
| Yang et al., _Toward Efficient Agents_ (survey) | 2601.14192 | Define eficiência como desempenho sob orçamento fixo ou custo menor com o mesmo desempenho. | Taxonomia: memória, ferramentas e planejamento. |

## 3. As cinco frentes da academia

### 3.1 Raciocínio mais curto

| Referência | arXiv | Achado | Benchmark |
| --- | --- | --- | --- |
| Cuadron et al., _The Danger of Overthinking_ | 2502.08235 | Em 4.018 trajetórias, mais overthinking significa menos desempenho. Escolher a solução de menor overthinking melhora quase 30% e corta 43% do custo. | SWE-bench Verified |
| Yang, _Chain of Draft for Software Engineering_ | 2506.10987 | Usa 55,4% dos tokens do CoT, com cerca de 45% menos custo e mais de 90% da qualidade. | SWE-bench (300 amostras) |
| Xu et al., _Chain of Draft_ | 2502.18600 | Iguala o CoT com apenas 7,6% dos tokens, no melhor caso. | Raciocínio, sobretudo math |
| Yang et al., DEER (early exit) | 2504.15895 | Sem treino. CoT de 19,1% a 80,1% mais curto, com acurácia de +0,3 a +5,0 pontos. | 10 benchmarks, 11 modelos |
| Ghosal et al., _Does Thinking More Always Help?_ | 2506.04210 | O desempenho sobe e depois cai com mais thinking. Tentativas paralelas com voto ganham até 20% com o mesmo orçamento. | Vários |
| Ma et al., _Reasoning Models Can Be Effective Without Thinking_ | 2504.09858 | Sem thinking, o modelo venceu com o mesmo número de tokens: 51,3 contra 28,9 no AMC 23, com 700 tokens. | 7 datasets |
| Han et al., TALE | 2412.18547 | Um orçamento no prompt comprime o CoT, mas um valor mal calibrado falha. | Raciocínio |
| Chen et al., _Do NOT Think That Much for 2+3=?_ | 2412.21187 | Modelos de raciocínio pensam demais em tarefas triviais. | GSM8K, MATH500, GPQA, AIME |
| Surveys: Sui et al. 2503.16419, Feng et al. 2504.10903, Wang et al. 2503.24377 | — | Separam três eixos: raciocínio mais curto, modelo menor e decodificação mais rápida. | — |

Leitura: em código, o ganho é cerca de metade do que aparece em math. O Chain of Draft cai de 7,6% para 55,4% dos tokens. No Claude Code, o usuário controla só o `effort`.

### 3.2 Menos observação no contexto

| Referência | arXiv | Achado | Benchmark |
| --- | --- | --- | --- |
| Wang et al., SWE-Pruner | 2601.16746 | Corta de 23% a 54% dos tokens do agente, com sucesso maior. Poda guiada pelo objetivo da tarefa. | SWE-bench Verified, LongCodeQA |
| Wang et al., SWE-Pruner Pro | 2607.18213 | Até 39% menos tokens e +3,8 pontos de resolução. Exige as representações internas do modelo. | SWE-bench Verified, Oolong |
| Kovács, Squeez | 2604.04979 | Um modelo de 2B devolve só o trecho relevante da saída de ferramenta. Remove 92% dos tokens de entrada, com recall de 0,86. | 618 exemplos de teste |
| Fan et al., _Harness Design for Coding Agents_ | 2609.20804 | Planejar corta custo em modelo forte, quase sem mudar a acurácia. Um harness só com bash custa bem menos. | SWE-bench Verified, Terminal-Bench 2.1 |
| Lumer et al., _Don't Break the Cache_ | 2601.06007 | Prefixo estável, com o conteúdo dinâmico no fim, corta de 41% a 80% do custo de API. | DeepResearch Bench, mais de 500 sessões |
| Liu et al., SimpleMem | 2601.02553 | Memória comprimida usa até 30x menos tokens, com F1 +26,4% no LoCoMo. | LoCoMo (conversa) |
| Li et al., Self-Route | 2407.16833 | Contexto longo vence em qualidade, mas RAG custa muito menos. Rotear entre os dois mantém a qualidade. | 3 LLMs |

### 3.3 Contexto compartilhado entre agentes

| Referência | arXiv | Achado | Aplicável ao Claude via API? |
| --- | --- | --- | --- |
| Parakhin, _Token Coherence_ | 2603.15183 | Adapta o protocolo MESI de cache: cada agente recebe a versão de um artefato e só o artefato alterado é reenviado. Economiza de 95,0% a cerca de 81% dos tokens, conforme a volatilidade. | Sim, como desenho. Mas é só simulação, de autor único. |
| Ye et al., KVCOMM | 2510.12872 | Reusa mais de 70% do KV cache entre agentes. Prefill até 7,8x mais rápido. | Não. Exige servidor de inferência próprio. |
| Bian et al., TokenDance | 2604.03143 | Armazenamento de KV por agente até 17,5x menor. | Não. Exige servidor próprio. |

Nenhum trabalho mede, em agentes de código reais, o contexto compartilhado entre subagentes para evitar releitura. Nossa M6 seria contribuição nova.

### 3.4 Delegar a modelos menores

| Referência | arXiv | Achado | Benchmark |
| --- | --- | --- | --- |
| Paul e Nandy, AgentRouter | 2609.22951 | Roteia **por passo**, com um classificador de 12M parâmetros. Custo 72% menor, com 97,3% da qualidade. Mandar todo passo ao modelo de fronteira desperdiça de 60% a 80% do orçamento. RouteLLM e FrugalGPT aplicados por passo cortam só 31% e 44%. | 50 mil passos anotados, não SWE-bench |
| Narayan et al., Minions (ICML 2025) | 2502.15964 | O modelo forte decompõe e o modelo local executa subtarefas em paralelo: custo 5,7x menor, com 97,9% do desempenho. A conversa livre com o modelo fraco cai para 87%. | Documentos longos |
| Belcak et al. (NVIDIA), _SLMs are the Future of Agentic AI_ | 2506.02153 | Posição: modelos pequenos bastam para chamadas estreitas e repetitivas. | Sem experimento |
| Jhandi et al. (AWS) | 2512.15943 | Um modelo de 350M ajustado faz 77,55% no ToolBench, contra 26,00% do ChatGPT-CoT. | ToolBench |
| Qian et al., xRouter | 2510.08439 | Um roteador pequeno treinado por RL ainda tem dificuldade com orquestração complexa. | — |
| Zhang et al., BoPO | 2602.21227 | Rotear por passo é problema sequencial: um erro cedo se acumula. Exige orçamento por tarefa. | — |

### 3.5 Orçamento visível e alocação por risco

| Referência | arXiv | Achado |
| --- | --- | --- |
| Liu et al., BATS / Budget Tracker | 2511.17006 | Dar mais orçamento de tool calls não ajuda se o agente não sabe quanto resta. Mostrar o saldo no contexto melhora a fronteira de Pareto. |
| He et al., _Consequence-Aware Compute Allocation_ | 2606.04402 | Aloque o modelo caro pela consequência da falha, não só pela dificuldade. |

## 4. O que está sustentado, o que é contestado

**Sustentado:**

- O custo de um agente vem de muitos passos e da releitura do contexto, não de um passo caro.
- Podar saídas de ferramenta e manter o prefixo estável dão os maiores cortes: de 23% a 80%.
- Pensar mais tem retorno decrescente e depois negativo.
- Um modelo forte que decompõe e um modelo barato que executa subtarefas isoladas mantêm perto de 98% da qualidade.

**Contestado:**

- O tamanho do ganho em código. Os números de math não se transferem.
- O roteamento aprendido por passo. O AgentRouter é um preprint único e sem replicação. O xRouter mostra fragilidade.
- Se vale mais limitar o comprimento do raciocínio ou fazer tentativas curtas em paralelo.

**Lacunas:**

- Ninguém mede o custo por issue resolvida com roteamento por passo no SWE-bench.
- Não há benchmark de Pareto para planejador forte com executor barato em código.
- Não há medida de contexto compartilhado entre subagentes de código reais.

## 5. Consequências para o SB

| Hipótese ou decisão | Evidência nova | Ajuste sugerido |
| --- | --- | --- |
| D1 da RFC-002 (pacote de contexto) | Token Coherence, _Don't Break the Cache_ | Versione cada arquivo por hash e reenvie só o que mudou (o pacote já marca "mudou"). Injete o pacote no fim do contexto, nunca no prefixo. |
| D2 (Explore em Haiku) e o advisor | Minions, AgentRouter | Delegue subtarefas isoladas. Não converse em vários turnos com o modelo fraco. |
| D3 e H4 (custo por turno) | Bai et al., SWE-Pruner, Squeez | Um hook `PostToolUse` pode podar saída de ferramenta por objetivo. É a próxima hipótese a testar. |
| `effort` dos subagentes | Cuadron, Chain of Draft SE, DEER | Use `effort` baixo em subagente mecânico. Espere cerca de 45% de ganho em código, não 90%. |
| Teto por tarefa | SWE-Effi, BATS | Mostre o orçamento restante ao agente. Pare o agente preso. |

## 6. Fontes

Todas em `https://arxiv.org/abs/<id>`, abertas em 2026-10-26: 2604.22750, 2509.09853, 2407.01502, 2601.14192, 2502.08235, 2506.10987, 2502.18600, 2504.15895, 2506.04210, 2504.09858, 2412.18547, 2412.21187, 2503.16419, 2504.10903, 2503.24377, 2601.16746, 2607.18213, 2604.04979, 2609.20804, 2601.06007, 2601.02553, 2407.16833, 2603.15183, 2510.12872, 2604.03143, 2609.22951, 2502.15964, 2506.02153, 2512.15943, 2510.08439, 2602.21227, 2511.17006, 2606.04402.

Também apareceram (2501.19393 s1, 2503.04697 L1, 2501.12599 Kimi k1.5). Eles tratam de treino do modelo e não mudam nada para o usuário do Claude Code.

## 🔗 Conexões

- [[Estudo - Orquestração de Agentes e Economia de Tokens]]
- [[Estudo - Roteamento para Modelos Menores - Advisor e Roteadores Externos]]
- [[RFC-002 - Orquestração de Agentes com Orçamento de Tokens]]
- [[RFC-001 - Memória de Agentes sobre o Second Brain com Orçamento de Tokens]]
