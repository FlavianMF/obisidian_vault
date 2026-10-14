---
title: Golden Set para Avaliar Retrieval de Memória do Agente
type: pattern
tags: [agentic-ai, evaluation, retrieval, second-brain, benchmark, tokens, methodology]
created: 2026-10-14
provenance: second-brain-sync
verified: 2026-10-14 via leitura das fontes citadas (abstracts/READMEs) e cálculo local dos intervalos de Wilson
confidence: low
scope: global
---

# Golden Set para Avaliar Retrieval de Memória do Agente

**Decidir grep vs embeddings vs híbrido exige um conjunto fixo de perguntas com a
nota-alvo anotada à mão e um harness que roda cada método sobre ele, medindo acerto e
tokens.** Sem isso a escolha é opinião. Este é o desenho mínimo, local-first, para o vault.

## O que é e o que não é

- **Golden set**: lista curada de `(query, notas relevantes)` rotulada por humano. Mede o
  *seu* corpus e o *seu* jeito de perguntar.
- **Benchmark público** (BEIR, 18 datasets): mede generalização entre domínios; o BM25
  segue baseline forte nele ([BEIR]). Não diz nada sobre este vault.
- **Teste unitário**: saída determinística, passa ou falha. Retrieval é graduado e
  estatístico: reporta taxa com intervalo, não verde/vermelho.
- Mesma filosofia de [[Detector Determinístico Fora do LLM como Piso de Qualidade]]: o que
  é mecânico (a nota certa apareceu no top-k?) é medido por código, sem LLM.

## Como construir

1. **Fontes das queries** (misture): (a) logs reais de sessão: perguntas que o usuário fez
   e o que o agente acabou abrindo; (b) sintéticas: LLM gera perguntas a partir de cada
   nota, humano valida/descarta ([Husain] recomenda sintético filtrado + revisão humana);
   (c) manuais, escritas de memória sem olhar a nota.
2. **Rótulos**: por query, `relevant` com grau 2 (nota que resolve) e 1 (ajuda). Pergunta
   deve ser inequívoca: dois revisores concordam sobre a nota certa ([Anthropic-evals]).
3. **Evitar vazamento**: proibido usar o título da nota como query. Marcar `kind`:
   `lexical` (ainda usa termos da nota), `paraphrase` (sinônimos/outro idioma),
   `multihop` (precisa de 2 notas), `negative` (nada no vault). Incluir negativas evita
   método que "sempre acha algo" ([Anthropic-evals]: balancear casos positivos e negativos).
4. **Split**: ~70% dev (para ajustar), ~30% held-out (só para a decisão final).
5. **Envelhecimento**: o vault cresce e distratores aumentam; nota renomeada quebra rótulo.
   Guardar `vault_commit` por query; revalidar a cada +20% de notas ou trimestre; query
   cuja nota sumiu vai para `status: retired`. Falha real nova vira query nova.

## Tamanho mínimo (estatística)

Intervalo de Wilson 95% para uma taxa de acerto (calculado localmente):

| n queries | p obs. 50% | p obs. 80% |
|---|---|---|
| 30 | 33–67% | 63–90% |
| 50 | 37–63% | 67–89% |
| 100 | 40–60% | 71–87% |

Com 30 queries só se distinguem métodos distantes ~15+ pontos; a comparação pareada
(mesmas queries) é mais sensível que comparar dois intervalos soltos. Buckley & Voorhees
(2000): "pelo menos 25 queries, 50 é melhor"; P@10 exige "muito mais que 50" ([B&V]).
Meta: 30 (MVP) → 60 → 100.

## Métricas

- Retrieval: **recall@k** (k=3,5,10), **precision@k**, **hit rate@k**, **MRR**,
  **nDCG@k** (usa graus 1/2). Com 1 nota-alvo por query, recall@k = hit rate@k.
  `[NÃO-VERIFICADO: definições são padrão da área; não abri fonte primária]`
- Resposta/faithfulness: RAGAS (avaliação sem resposta de referência, cobre retrieval e uso
  do contexto [RAGAS]); ARES (juízes LM leves + poucas centenas de anotações humanas com
  prediction-powered inference [ARES]); TruLens "RAG triad": context relevance,
  groundedness, answer relevance [TruLens]. Fase 3, não agora.
- **LLM-as-judge**: concorda >80% com humanos em chat, mas tem vieses de posição,
  verbosidade e autoelogio [Zheng]. Calibrar contra rótulos humanos e rechecar
  periodicamente [Husain]. Reportar precision/recall do juiz, não só concordância bruta.
- **Métrica-chave do projeto**: `tokens_por_acerto = tokens_totais / queries_resolvidas`
  e `custo_por_tarefa_resolvida`. Tokens = saída do método (linhas de manifest) + notas
  abertas pelo agente. A Anthropic recomenda rastrear tokens, custo por tarefa e latência
  na mesma banca de tarefas [Anthropic-evals]. Contar tokens por estimativa fixa
  (chars/3,5) e declarar isso; trocar por tokenizer real depois.
- `pass@k` (alguma tentativa acerta) vs `pass^k` (todas acertam) quando o agente repete
  a busca [Anthropic-evals].

## Ferramentas

- **Leve (recomendado)**: pytest + `golden.jsonl` + métricas em Python puro (~30 linhas).
  `ranx` quando precisar de nDCG/MRR validados e testes pareados (t-test, Fisher, Tukey;
  MIT, `pip install ranx`) [ranx]. `ir_measures` (nDCG, RR, P@k; qrels e runs em dict)
  é alternativa [ir_measures].
- **Pesado (adiar)**: RAGAS/ARES/TruLens, só para faithfulness da resposta final.
- Híbrido: Anthropic reporta embeddings+BM25 melhor que embeddings sozinhos; falhas no
  top-20 de 5,7% → 2,9% com contextual embeddings+BM25 e 1,9% com reranking
  [Contextual-Retrieval]. Corpus e idioma deles diferem do vault: não extrapolar.

## Proposta para este vault

**Arquivos** (versionados no repo do vault):

```
00_META/eval/golden.jsonl      # uma query por linha
00_META/eval/run_eval.py       # CLI do harness
00_META/eval/runs/             # resultados por execução (gitignore)
```

**Schema de `golden.jsonl`:**

```json
{"id":"q001","query":"...","lang":"pt","kind":"paraphrase",
 "source":"manual|log|synthetic","repo":null,
 "relevant":[{"path":"20_Permanent_Notes/X.md","grade":2}],
 "split":"dev|test","vault_commit":"7537a9c","status":"active",
 "created":"2026-10-14","notes":""}
```

**Harness** (`python run_eval.py --methods grep,fts5,embed,hybrid --split dev --k 5`):
cada método é um adaptador `search(query) -> [(path, score)]` + `cost(query) -> tokens`:

- `grep`: termos da query com `rg` em `00_META/manifests/by_type/*.md`, ranking por nº de
  termos casados (replica o uso atual).
- `hint`: `session_hint.sh <repo>`, só para queries com `repo` (não é busca por query).
- `fts5`: SQLite FTS5/BM25 sobre título+tags+path (stdlib, zero dependência).
- `embed`: modelo multilíngue local (Ollama ou sentence-transformers) sobre título+tags+
  primeiro parágrafo. `[NÃO-VERIFICADO: escolha do modelo; testar em PT]`
- `hybrid`: fusão por RRF de `fts5` + `embed`.

Saída: tabela por método com recall@3/5/10, MRR, nDCG@10, hit rate, tokens médios,
**tokens por acerto**, latência e intervalo de confiança (bootstrap). Regra de decisão
escrita antes de rodar: adotar embeddings/híbrido só se recall@5 melhorar com intervalo
claro no held-out E tokens por acerto não piorar mais que o limite combinado.
Incluir sempre um **baseline degenerado** (resultado aleatório, e top-k fixo), conforme
[[Benchmark Sem Baseline Degenerado Não Diz Quanto do Score é Capacidade]].

## 15 queries-exemplo (notas-alvo reais; já parafraseadas)

| id | query | kind | nota-alvo |
|---|---|---|---|
| q01 | subir 200 tarefas no Jira sem passar pelo assistente de CSV | paraphrase | Importar Issues no JIRA por REST em vez do Assistente de CSV |
| q02 | por que o campo Parent do importador do Jira não aceita a chave da issue | lexical | Importador CSV do JIRA - Parent Aponta Issue ID do Arquivo, Não a Chave |
| q03 | mandei num_ctx na request e o modelo local ignorou | lexical | Ollama Ignora Tamanho de Contexto Enviado por Request |
| q04 | how to read a running Ollama model's context window | paraphrase (EN) | Detecção Ao Vivo de Janela de Contexto do Ollama via api-ps e api-show |
| q05 | publiquei a tag de release mas a develop não recebeu | paraphrase | Tag de Release Não Volta Pra Develop Sozinha |
| q06 | chromium via snap não abre sem tela no WSL | paraphrase | Chrome Headless em WSL2 - .deb Oficial, Não apt chromium |
| q07 | o claude plugin mexeu no meu settings.json do dotfiles | paraphrase | Claude Plugin CLI Reescreve o settings.json Symlinkado do Repo |
| q08 | devo usar Taste ou impeccable para redesenhar esta tela | multihop | Skills de Design se Contradizem Entre Si, Dentro e Fora do Pacote (+ MOC Design de Interface com Agente no grau 1) |
| q09 | duas sessões do agente escreveram no índice e uma perdeu o dado | paraphrase | Sessões Paralelas Perdem Escrita no Índice Compartilhado |
| q10 | rádio não reconhece o iPod emulado por USB | paraphrase | iAP sobre USB HID - Report Exige Byte de Link Control |
| q11 | como saber quanto do score de um benchmark vem do modelo e quanto do formato | paraphrase | Benchmark Sem Baseline Degenerado Não Diz Quanto do Score é Capacidade |
| q12 | quando virar regra mecânica em vez de instrução no prompt | paraphrase | Detector Determinístico Fora do LLM como Piso de Qualidade (+ Regra Gradual é Ignorada pelo Agente, Regra Binária é Obedecida no grau 1) |
| q13 | CI de cobertura falhando depois que excluí arquivos | paraphrase | Gate de Cobertura Tem Que Excluir do Numerador E do Denominador, Não Só Relaxar o Limiar |
| q14 | skill enorme consome contexto antes de começar | paraphrase | Skill Monolítica Gasta o Contexto Antes de a Tarefa Começar |
| q15 | receita de pão de queijo | negative | (nenhuma; o método deve devolver vazio/baixa confiança) |

Os 14 `path`s foram conferidos com `ls` em 2026-10-14 (todos existem). Antes de congelar o
`golden.jsonl`, conferir se não há 2ª nota que também resolve a query (rotular grau 1).

## Plano de evolução

1. **Semana 1**: 30 queries (15 manuais, 10 de logs reais, 5 negativas/multihop); harness
   com `grep` + `fts5`; baseline degenerado; medir tokens.
2. **Semana 2-3**: adaptador `embed` + `hybrid`; split dev/test; intervalos por bootstrap;
   aplicar a regra de decisão ao held-out.
3. **Mês 2**: crescer para 60-100 queries (sintéticas validadas); revalidar `vault_commit`;
   rodar no CI do vault ou como hook manual após `generate_manifests.py`.
4. **Depois**: juiz LLM para faithfulness da resposta final, calibrado com ~50 rótulos
   humanos; `pass^k` para estabilidade; monitorar saturação (>90% vira só regressão)
   [Anthropic-evals].

## Fontes

- [BEIR] Thakur, Reimers, Rücklé, Srivastava, Gurevych (2021). *BEIR: A Heterogenous
  Benchmark for Zero-shot Evaluation of Information Retrieval Models*.
  https://arxiv.org/abs/2104.08663 [VERIFICADO: abstract]
- [B&V] Buckley & Voorhees (2000). *Evaluating evaluation measure stability*, SIGIR.
  https://nist.gov/publications/evaluating-evaluation-measure-stability [VERIFICADO: abstract]
- [RAGAS] Es, James, Espinosa-Anke, Schockaert (2023). *Ragas: Automated Evaluation of
  Retrieval Augmented Generation*. https://arxiv.org/abs/2309.15217 [VERIFICADO: abstract]
- [ARES] Saad-Falcon, Khattab, Potts, Zaharia (2023/NAACL 2024). *ARES: An Automated
  Evaluation Framework for Retrieval-Augmented Generation Systems*.
  https://arxiv.org/abs/2311.09476 [VERIFICADO: abstract]
- [Zheng] Zheng et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*,
  NeurIPS D&B. https://arxiv.org/abs/2306.05685 [VERIFICADO: abstract; números de
  consistência de posição vistos só em snippet de busca, não citados aqui]
- [TruLens] TruLens docs, *RAG triad*.
  https://www.trulens.org/getting_started/core_concepts/rag_triad/ [VERIFICADO]
- [Anthropic-evals] Anthropic Engineering, *Demystifying evals for AI agents*.
  https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents [VERIFICADO]
- [Contextual-Retrieval] Anthropic, *Introducing Contextual Retrieval*.
  https://www.anthropic.com/news/contextual-retrieval [VERIFICADO]
- [Husain] Hamel Husain, *Your AI Product Needs Evals*. https://hamel.dev/blog/posts/evals/
  [VERIFICADO]
- [ranx] Bassani, *ranx* (ECIR 2022 para o paper; repositório MIT).
  https://github.com/AmenRa/ranx [VERIFICADO: README; paper ECIR não aberto]
- [ir_measures] Terrier Team (Glasgow). https://github.com/terrierteam/ir_measures
  [VERIFICADO: README]

## 🔗 Conexões

- [[Benchmark Sem Baseline Degenerado Não Diz Quanto do Score é Capacidade]]
- [[Detector Determinístico Fora do LLM como Piso de Qualidade]]
- [[Skill Monolítica Gasta o Contexto Antes de a Tarefa Começar]]
- [[Métricas de Avaliação de Geração de Artefato de Engenharia por LLM]]
- [[Benchmark Neutro de Fornecedor via Adaptador MCP]]
- [[00_META/Frontmatter-Schema]]
