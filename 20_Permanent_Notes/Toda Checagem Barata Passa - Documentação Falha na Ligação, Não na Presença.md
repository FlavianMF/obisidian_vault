---
title: Toda Checagem Barata Passa - Documentação Falha na Ligação, Não na Presença
type: pattern
tags: [documentation, verification, code-review, grading, agentic-ai]
created: 2026-09-17
provenance: correcoes_docs_tcc
project: correcoes_docs_tcc
verified: 2026-09-17 via leitura das 16 avaliações e das 8 entradas de docs/playbook.md
---

# Toda Checagem Barata Passa - Documentação Falha na Ligação, Não na Presença

Corrigir a documentação de 16 repositórios de TCC produziu oito armadilhas catalogadas que parecem
oito problemas diferentes. São um só. Em todas elas o `grep` acha o termo citado, o arquivo existe
no caminho escrito, o link não está quebrado, e cada bloco do README é internamente coerente. **O
que falha é a ligação entre duas coisas que passam individualmente.**

Por isso a leitura linear não denuncia: ela verifica presença, e presença está toda lá.

## As juntas que quebram

| Ligação | Caso real |
|---|---|
| afirmação ↔ artefato | tabela de pinagem do README diverge do firmware em 3 de 9 pinos |
| passo N ↔ passo N+1 | o passo que manda sobrescrever o arquivo apaga as variáveis que o passo anterior mandou escrever |
| função ↔ chamador | `find_csv()` implementa exatamente o que o `.md` promete; o único chamador sempre passa caminho fixo, e o `or` nunca cai no segundo operando |
| manifesto ↔ commit | `ambiente.json` declara `revisao_base_git` três commits atrás do estado que descreve |
| documento ↔ documento | o PDF da entrega descreve outra árvore, outro ponto de entrada e outra pinagem que o repositório atual |
| instrução ↔ mecanismo vivo | o `.md` manda editar um `#define` que uma PR moveu para Kconfig: a instrução não falha, só não tem efeito |
| dependência declarada ↔ dependência importada | `requirements.txt` com 136 pacotes fixados e nenhum dos quatro que o código importa |
| negativa ↔ árvore | o README afirma que um alvo "não existe neste checkout" e o arquivo está lá |

## A consequência de método

**Verificação por presença não encontra nada. Só a verificação por ligação encontra.** Quem audita
documentação — professor, revisor de PR ou agente — não pode parar em "o termo aparece no código".
Cada junta tem um teste barato e específico:

- afirmação de comportamento: não se confirma achando a função, **confirma-se achando o chamador**;
- passo de configuração: procurar o passo posterior que sobrescreve o arquivo do passo anterior, e o
  pacote que a documentação instala e nenhum comando usa (sintoma de linha apagada na edição);
- manifesto de evidência: comparar o sha declarado com o commit avaliado antes de acreditar no resto;
- dependência: cruzar o arquivo de dependências com os `import` reais, não com o que o README diz;
- árvore e diagrama: procurar o módulo órfão — arquivo grande e integrado que nenhum documento cita.

O corolário desagradável: **um agente é ótimo em produzir prosa plausível sobre presença**. Foi por
isso que a correção exigiu `arquivo:linha` em toda linha e a busca que provou cada ausência — ver
[[Rubrica em Prosa Vira Gabarito de Evidência]].

## O espelho

[[Documentação Desatualizada é Bug, Não Dívida]] é a mesma verdade pelo lado de quem escreve: a doc
apodrece porque a ligação com o código se rompe sem barulho, e nenhum teste quebra. Esta nota é o
lado de quem lê: **provar que apodreceu custa uma junta de cada vez**, e é a única prova que
sobrevive a uma contestação.

## 🔗 Conexões
- [[Rubrica em Prosa Vira Gabarito de Evidência]]
- [[Documentação Desatualizada é Bug, Não Dívida]]
- [[Notas de Análise Envelhecem em Dias - Reverificar no Código Antes de Apresentar]]
- [[correcoes_docs_tcc]]
