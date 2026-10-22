---
title: STE-80 - Escrita Controlada para Agentes em Português
type: pattern
tags: [prompt-engineering, agentic-ai, technical-writing, controlled-language, claude-code, hooks]
created: 2026-10-22
provenance: obsidian_vault
verified: 2026-10-22 via análise das fontes da nota ASD-STE100 e leitura de ~/dotfiles/agents/AGENTS.md e da skill caveman (sem teste próprio ainda)
confidence: low
seen_in: [obsidian_vault]
---

# STE-80 - Escrita Controlada para Agentes em Português

**O "80%" do ASD-STE100 são as regras de estrutura: frase, verbo, parágrafo e termo. Os 20%
que ficam de fora são o dicionário controlado.** O dicionário é o que apaga fatos de domínio,
e ele não existe em português. A outra decisão: "80%" é a **meta de medição**, não a
instrução. A instrução ao agente é binária. Um linter fora do modelo mede quanto do texto
passa.

## Definição operacional de "80%"

O STE-80 está implementado quando, numa bateria fixa de prompts:

1. **≥ 80% das frases** passam no linter (tamanho, voz, tempo verbal, pontuação).
2. **Nenhum fato se perde** em relação à resposta sem estilo. Este critério é absoluto.
3. A resposta inteira não fica mais longa que a resposta sem estilo.

O critério 2 existe por causa do teste de Ghinda: o nome da norma no prompt apagou 46,8% dos
fatos. Ver [[ASD-STE100 Simplified Technical English]].

## As regras que entram, já em português

O STE é inglês. As regras de estrutura passam para o português. O dicionário não passa.

| STE | Regra STE-80 em PT-BR | Exemplo |
|---|---|---|
| 5.1 / 6.3 | Frase com no máximo 20 palavras em instrução e 25 em explicação. Código, caminho, número com unidade e sigla contam como uma palavra (8.6). | — |
| 5.2 / 5.3 | Uma instrução por frase, no imperativo. | "Rode os testes." Não: "Você deve rodar os testes e depois commitar." |
| 5.4 | Condição antes do comando, com vírgula. | "Se o teste falhar, leia o log." |
| 3.6 | Voz ativa. Sem passiva analítica nem pronominal em instrução. | Não: "O arquivo foi removido pelo script." Não: "Remove-se o cache." |
| 3.5 | Sem gerúndio fora de nome técnico. Sem gerundismo. | Não: "vou estar verificando", "verificando o log, nota-se". |
| 3.2 / 3.4 | Presente, pretérito perfeito, futuro simples e imperativo. Evitar futuro do pretérito e tempos compostos. | "O hook roda no Stop." Não: "O hook teria sido executado". |
| 3.7 | Verbo para ação, não substantivo. **É a regra que mais rende em português**, porque o português técnico nominaliza muito. | "Verifique a configuração." Não: "Realize a verificação da configuração." |
| 2.1 | No máximo duas preposições "de" encadeadas num sintagma. | Não: "o arquivo de configuração do servidor de produção do cliente". |
| 4.1 / 6.1 | Um tópico por frase. | — |
| 6.4–6.6 | Parágrafo começa pela frase-tópico, trata de um tópico e tem no máximo 6 frases. | — |
| 4.3 | Texto complexo vira lista vertical. A primeira linha termina em dois-pontos. | — |
| 1.11 / 1.3 | Um termo por coisa, sem alternar sinônimos. Termo de domínio fica como está. | Não alternar "hook", "gancho" e "gatilho". |
| 4.2 | Mantenha as palavras necessárias. Sem frase telegráfica que admita duas leituras. | — |
| 8.1 | Sem ponto e vírgula. Escreva duas frases. | — |
| Modais | "deve" = obrigação, "pode" = capacidade. Incerteza real é dita uma vez, sem empilhar ("talvez possa eventualmente"). | — |
| 7.1–7.3 | Aviso: palavra de risco, comando, consequência. | "AVISO: não rode `git reset --hard` agora. As mudanças não salvas serão perdidas." |
| 5.5 | Nota só informa. Instrução nunca fica dentro de nota. | — |

**Ficam de fora (os 20%):** o dicionário de ~900 palavras (1.1, 1.2, 1.4, 9.2), as
categorias de nome e verbo técnico (1.5, 1.12), a ortografia americana (1.14) e as
MAIÚSCULAS. No lugar delas, entra uma regra só: **nome de código, produto, comando e conceito
de domínio fica literal, nunca é parafraseado.**

**Isenções:** blocos de código, saída de ferramenta, citação, mensagem de erro, texto que o
usuário pediu na própria voz e texto acadêmico. O texto acadêmico tem suas próprias regras
(ver [[Escrita Acadêmica de Alto Impacto]]).

## Arquitetura em camadas

O vault já registra a ordem: o que um binário verifica sai do prompt. O que fica no prompt é
escrito como contagem ([[Regra Gradual é Ignorada pelo Agente, Regra Binária é Obedecida]],
[[Detector Determinístico Fora do LLM como Piso de Qualidade]]).

1. **Instrução (sempre carregada):** um bloco curto e binário em
   `~/dotfiles/agents/AGENTS.md`. Esse arquivo é a fonte única para Claude Code, Codex e
   OpenCode. O bloco tem cerca de 15 linhas: as regras da tabela, a regra de fato literal e as
   isenções. O bloco não cita "ASD-STE100" como ordem, porque o nome da norma puxa o
   dicionário e apaga fatos.
2. **Linter determinístico:** um script stdlib, `ste_lint.py`, para PT e EN. Ele remove
   código, caminhos e URLs antes de contar. Ele mede frase > 20/25, parágrafo > 6 frases,
   ponto e vírgula, passiva (`foi|foram|é|são|será|serão` + particípio, e `-se` enclítico em
   verbo transitivo), gerúndio (`\w+ndo\b` com lista de exceções), nominalização
   (`realizar|efetuar|fazer|proceder` + substantivo em `-ção|-mento`) e modais empilhados. A
   saída é a porcentagem de frases conformes e a lista de violações com o número da regra.
3. **Hook Stop em modo sombra:** o hook lê a última resposta no transcript, roda o linter e
   grava uma linha em jsonl local. Ele não escreve no contexto. É o mesmo desenho do hook
   `jev-e`. Bloquear com `exit 2` vem só depois da linha de base, porque o bloqueio custa uma
   geração nova a cada falha.
4. **Skill estrita para documentos:** README, runbook, mensagem de erro e procedimento. Ela
   carrega exemplos de antes e depois e roda o linter em modo `procedural` ou `descriptive`.
   Ela só carrega quando a tarefa pede.
5. **Eval:** de 8 a 10 prompts fixos (explicar código, procedimento, diagnóstico de bug),
   duas condições (sem estilo, STE-80) e 2 execuções cada. Cada prompt tem uma lista de fatos
   esperados. O critério de aceite é o da definição operacional acima.

## Conflito com a skill caveman

A skill caveman já declara "ASD-STE100 is the floor". Ela pede 20 palavras, voz ativa,
imperativo e um termo por coisa. Mas ela também solta artigos e aceita fragmentos. Isso
contraria as regras 4.2 e 2.3 do STE. Há dois caminhos:

- O STE-80 vira o piso e a caveman só corta cerimônia. Nesse caso, os artigos voltam.
- A caveman continua no chat, e o STE-80 vale só para texto persistido (docs, commits,
  notas). A própria caveman já exige prosa normal nesses casos.

A escolha é do usuário. As duas regras não podem valer ao mesmo tempo sobre artigo e
fragmento.

## O que NÃO funcionou

- **Nomear a norma no prompt:** "escreva em ASD-STE100" apagou 46,8% dos fatos de código no
  teste de Ghinda (Claude). O pedido frouxo apagou 8,5%. O pedido "80% of the way" manteve
  8 de 8 fatos no teste da StashBase.
- **Instrução gradual:** "frases curtas quando possível" é negociada pelo modelo. O "80%"
  escrito no prompt é o mesmo tipo de regra gradual.
- **Autoavaliação:** o modelo superestima a própria conformidade (dois preprints de 2026).
  Quem mede é o linter, não o modelo.
- **Só o linter:** a skill SimpleEnglish descobriu numa auditoria (2026-09-02) que o linter
  media obediência à regra, não o que o leitor vê. Ela passou a contar também negrito,
  cabeçalho, bullets e travessão.
- **Output style sem `keep-coding-instructions: true`:** remove as instruções de código do
  Claude Code.

Nenhum destes itens foi reproduzido neste ambiente ainda. A nota fica em `confidence: low`
até o eval da camada 5 rodar.

## 🔗 Conexões

- [[ASD-STE100 Simplified Technical English]] — a norma e as fontes.
- [[Regra Gradual é Ignorada pelo Agente, Regra Binária é Obedecida]]
- [[Detector Determinístico Fora do LLM como Piso de Qualidade]]
- [[Slop de IA é Convergência de Treino, Não Falta de Gosto]]
- [[Aviso Longe do Comando Não é Lido - Corrija o Comando]] — a regra 7.2 do STE dita de
  outro jeito.
