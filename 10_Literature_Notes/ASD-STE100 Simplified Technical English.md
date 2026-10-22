---
title: ASD-STE100 Simplified Technical English (Issue 9)
type: literature
tags: [technical-writing, controlled-language, llm, prompt-engineering, aerospace, writing]
created: 2026-10-22
provenance: obsidian_vault
source: https://www.asd-ste100.org/
verified: 2026-10-22 via leitura das regras parafraseadas (0xpili/simplified-technical-english, Issue 7), Wikipedia, fact-check de max.nardit.com e posts de Ghinda e StashBase
confidence: low
seen_in: [obsidian_vault]
---

# 📖 ASD-STE100 Simplified Technical English

O **ASD-STE100** é uma língua natural controlada para documentação técnica. A ASD
(Aerospace, Security and Defence Industries Association of Europe) mantém a norma. O
objetivo é um texto que um leitor não nativo entende na primeira leitura, sem ambiguidade.
A norma controla **como** o conteúdo é dito. Ela não controla a formatação (fonte,
numeração).

## História e governança

- 1983: as companhias aéreas europeias pedem à AECMA um inglês controlado para manuais de
  manutenção. A AIA participa.
- 1985: sai o *AECMA Simplified English Guide*.
- 2004: a AECMA entra na ASD, e o guia vira a especificação ASD-STE100.
- 2013: a Issue 6 fica gratuita.
- **15 jan 2025: a Issue 9 vira norma internacional.** É a edição atual.
- O STEMG (Simplified Technical English Maintenance Group) mantém a norma. Uma edição nova
  sai mais ou menos a cada três anos.
- Em dez/2024, 64% dos usuários registrados estavam fora de aeroespacial e defesa
  (automotivo, energia, offshore, dispositivos médicos).

## Estrutura da norma

- **Parte 1: 53 regras de escrita em 9 seções.**
- **Parte 2: dicionário.** Cerca de 900 palavras aprovadas e cerca de 1.200 não aprovadas,
  cada uma com alternativa. Palavra aprovada aparece em MAIÚSCULAS. Cada palavra aprovada tem
  **uma classe gramatical e um sentido**. Exemplo: o verbo *close* tem dois sentidos
  permitidos; o adjetivo *close* vira *NEAR*.
- **Nomes técnicos e verbos técnicos** não estão no dicionário. São categorias definidas
  (Regras 1.5 e 1.12). O texto pode usar uma palavra fora do dicionário quando ela cabe numa
  dessas categorias (*propeller*, *to ream*).

## As 53 regras (paráfrase, numeração da Issue 7)

> Fonte: reescrita comunitária em `0xpili/simplified-technical-english`, baseada na Issue 7
> (2017). A Issue 9 mantém 53 regras em 9 seções. A numeração pode ter mudado: confira no PDF
> oficial antes de citar um número.

| Seção | Regras | Conteúdo |
|---|---|---|
| 1. Palavras | 1.1–1.14 | Só palavras aprovadas, nomes técnicos e verbos técnicos. Palavra só com a classe e o sentido aprovados. Nome técnico não vira verbo. Um nome técnico por item, sem alternar (1.11). Sem gíria nem jargão como nome. Verbo técnico não vira substantivo. Ortografia americana (1.14), salvo diretiva oficial contrária. |
| 2. Substantivos compostos | 2.1–2.3 | Cadeia de substantivos com no máximo 3 palavras. Nome longo: escreva por extenso uma vez, depois abrevie. Use artigo ou demonstrativo antes do substantivo. |
| 3. Verbos | 3.1–3.7 | Só infinitivo, imperativo, presente simples, passado simples, futuro e particípio como adjetivo. Sem verbos auxiliares para tempos compostos. Forma *-ing* só em nome técnico ou título. **Voz ativa obrigatória em procedimento**, e na maior parte da descrição. Use um verbo para mostrar ação, não um substantivo (3.7). |
| 4. Frases | 4.1–4.4 | Frase curta, específica, com um tópico. Mantenha as palavras necessárias, sem contração. Lista vertical para texto complexo. Palavras de conexão entre frases relacionadas. |
| 5. Procedimento | 5.1–5.5 | **Máx. 20 palavras por frase** (vale para avisos). **Uma instrução por frase**, salvo ações simultâneas. Imperativo. Condição antes do comando, separada por vírgula. Nota só informa: não dá instrução, máx. 25 palavras. |
| 6. Descrição | 6.1–6.6 | Informação em etapas, um tópico por frase. Palavras-chave repetidas para ligar frases. **Máx. 25 palavras por frase.** Parágrafo começa com frase-tópico. Um tópico por parágrafo. **Máx. 6 frases por parágrafo.** |
| 7. Segurança | 7.1–7.3 | Palavra de nível de risco (WARNING, CAUTION). Comece com comando ou condição clara. Explique o risco ou o resultado. |
| 8. Pontuação e contagem | 8.1–8.7 | **Sem ponto e vírgula.** Hífen liga palavras muito relacionadas. Parênteses só para referência, número de item, sigla e explicação curta. Número com unidade, sigla, identificador e texto citado contam como uma palavra. Grupo com hífen conta como uma palavra. |
| 9. Práticas | 9.1–9.4 | Se a troca palavra por palavra não basta, mude a construção e mantenha o sentido. Leia o sentido aprovado antes de usar. Sem *phrasal verbs*. Estilo consistente: mesmas palavras para o mesmo tipo de passo. |

**Modais (lista de erros recorrentes da Issue 9):** *shall* e *should* comuns viram *must*;
*may* vira *can*. A voz passiva, segundo o fact-check de Nardit, é aceita "só quando o agente
é desconhecido", não "quando necessário".

## Limitações e críticas

- Aplicar a norma corretamente é difícil. Redatores sem treino padronizaram usos
  agramaticais.
- Checadores (Boeing BSEC, HyperSTE, Congree, TechScribe, Acrolinx) não são infalíveis. A ASD
  não endossa nenhum.
- A própria ASD diz que o STE complementa um guia de estilo. Ele não o substitui.
- Fora de aeroespacial e defesa, o mais comum é *plain language*, não STE.
- No Brasil, o equivalente institucional é a [Lei 15.263/2025](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/Lei/L15263.htm)
  (Política Nacional de Linguagem Simples, 14 nov 2025). Ela vale para a administração
  pública e não define limites numéricos como o STE.

## STE e LLMs (estado em out/2026)

- **Karpathy, post no X de 2 out 2026:** pede às LLMs explicações em ASD-STE100 e diz que o
  texto fica mais legível. Às vezes pede **"80% of the way"**, porque a norma é rígida. É a
  origem do "STE-80".
- **Skills públicas:**
  - `0xpili/simplified-technical-english` (MIT): `SKILL.md`, 53 regras reescritas, 869
    palavras, tabela de substituições e `ste_check.py`. O checador mede tamanho de frase,
    parágrafo com mais de 6 frases, forma verbal e passiva, ponto e vírgula, contração e
    palavra fora da lista. Ele não confirma o sentido de uma palavra.
  - `AminBlg/SimpleEnglish`: dois registros. Respostas de chat em prosa sem cabeçalho,
    negrito ou travessão. Documentos com 20/25 palavras, voz ativa e sem *should/would/may/might*.
    Resultado próprio: violações por 100 palavras caíram de 4,09 para 0,91 (−78%). Defeitos
    visíveis em respostas caíram 95%. O juiz é Claude avaliando Claude, e a amostra é pequena
    (8 perguntas, 8 documentos).
  - Gist `toppa` (*output style* para Claude Code): tabela de regras com
    `keep-coding-instructions: true`, isenção para código e citações, glossário em
    `CONTEXT.md`, e a regra "clareza vence brevidade, sem perder fato nem ressalva".
- **Perda de fatos (Lucian Ghinda, ago/2026, informal):** Claude explicando código Ruby.
  Palavras por frase: 17,8 sem estilo, 9,1 com "Simple Technical English", 10,2 com
  ASD-STE100. **Fatos perdidos: 8,5% com o pedido frouxo e 46,8% com o nome da norma.** A
  causa provável: o dicionário não tem palavras para conceitos de domínio, então o modelo
  explica o conceito em vez de nomeá-lo, ou o omite. O teste da StashBase (prosa, Opus 5.5)
  manteve 8 de 8 fatos com "80% of the way". As respostas não ficaram mais curtas, só as
  frases.
- **O modelo gera "inglês com sabor de STE", não STE.** Ele quebra o vocabulário e parece
  conforme. Dois preprints de 2026 mostram que modelos superestimam a própria conformidade com
  restrições. A *cheat sheet* que circulou com o post de Karpathy tem erros de dicionário
  (*approximately* é aprovado, *TEST* é aprovado só como substantivo).

## Lacunas desta nota

- O texto oficial da Issue 9 não foi extraído. O PDF oficial é gratuito, mas vem protegido
  contra cópia. Toda regra acima é paráfrase.
- Os números de Ghinda para Codex divergem entre as fontes secundárias. Os dados brutos estão
  em `github.com/lucianghinda/llm-experiments/tree/main/simplified-technical-english`.

## 🔗 Conexões

- [[STE-80 - Escrita Controlada para Agentes em Português]] — como aplicar isto aos agentes.
- [[Regra Gradual é Ignorada pelo Agente, Regra Binária é Obedecida]] — por que o STE
  funciona com LLM: as regras são contáveis.
- [[Slop de IA é Convergência de Treino, Não Falta de Gosto]] — o que o STE corta.

## Fontes

- ASD-STE100 Issue 9 (PDF oficial): https://www.asd-ste100.org/
- Wikipedia: https://en.wikipedia.org/wiki/Simplified_Technical_English
- Fact-check do post de Karpathy: https://max.nardit.com/articles/karpathy-understanding-llm-outputs
- Ghinda: https://notes.ghinda.com/post/don-t-automatically-add-asd-ste100-to-your-agents-instructions
- StashBase (CLAUDE.md × output style × skill): https://stashbase.ai/blog/asd-ste100-claude/
- Skills: https://github.com/0xpili/simplified-technical-english ·
  https://github.com/AminBlg/SimpleEnglish · https://gist.github.com/toppa/bf7ff49d6fc44fd4fc3337248f8f2a7e
