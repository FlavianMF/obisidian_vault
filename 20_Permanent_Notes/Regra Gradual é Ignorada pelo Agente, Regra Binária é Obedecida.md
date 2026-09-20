---
title: Regra Gradual é Ignorada pelo Agente, Regra Binária é Obedecida
type: pattern
tags: [prompt-engineering, agentic-ai, quality, skills, design, checklist]
created: 2026-09-20
provenance: taste-skill
verified: 2026-09-20 via leitura de ~/.agents/skills/design-taste-frontend/SKILL.md linhas 253, 687-701, 910-979
---

# Regra Gradual é Ignorada pelo Agente, Regra Binária é Obedecida

**Instrução com grau embutido — "use com moderação", "evite exagerar", "prefira menos" —
é negociável, e o modelo negocia. A mesma regra escrita como limiar ou contagem sobrevive
à geração.** A [[Taste Skill]] registra isso como observação de campo, não como teoria, em
`SKILL.md:701`: *"The agent has historically ignored em-dash limits when phrased as 'use
sparingly.' The phrasing here is binary: zero em-dashes."*

A reescrita elimina toda via de escape: *"There is no 'limited use' allowance, no 'natural
language frequency' allowance, no 'in body copy is fine' allowance. None."* (`:687`), e a
proibição é enumerada por superfície — headline, eyebrow, pílula, texto de botão, legenda,
navegação, corpo, atribuição de citação — incluindo a meia-risca usada como separador.

## O mesmo movimento nas regras de layout

O que a v2 faz com o resto das regras é a mesma conversão, de julgamento para contagem:

- *eyebrow* falha quando `count > ceil(sectionCount / 3)`, contado por ocorrência de
  `uppercase tracking` no arquivo (`:253`, marcada como a regra mais violada em teste);
- o terceiro bloco consecutivo de imagem+texto alternados falha, não "desaconselha";
- bento com N itens exige exatamente N células, sem célula de enchimento;
- navegação em uma linha, altura máxima 80px;
- rótulo de CTA que quebra em duas linhas no desktop falha.

É por isso que o pre-flight de 62 caixas da v2 funciona onde o de 7 caixas da v1 não
funcionava. **Não é o tamanho da lista: é que cada item virou resolvível por contagem, e
uma caixa que não pode ser marcada com honestidade reprova a entrega inteira.**

## A tensão com o detector, que vale registrar

[[Detector Determinístico Fora do LLM como Piso de Qualidade]] parte da mesma observação e
vai para o lado oposto: se a regra é mecânica, ela deve **sair** do prompt e virar exit
code, porque regra em prompt é probabilística. As duas leituras são compatíveis, e a ordem
de preferência é clara:

1. Existe binário que checa? A regra sai do prompt. Custo de contexto zero, resposta igual
   sempre, e o mesmo artefato serve hook, CLI e CI.
2. Não existe? A regra fica no prompt, **mas escrita como limiar ou contagem**, nunca como
   advérbio. É o melhor que sobra, e é mensuravelmente melhor que a versão gradual.

## Generaliza

Vale para qualquer instrução durável de agente, não só design: convenção de commit, limite
de tamanho de função, proibição de dependência, formato de log. Ao revisar um `CLAUDE.md`,
uma skill ou uma rubrica, o teste é procurar os advérbios — cada "geralmente", "evite",
"prefira", "quando possível" é uma regra que o modelo vai negociar. Converter para número,
lista fechada ou condição booleana é barato e muda o resultado.

## 🔗 Conexões

- [[Detector Determinístico Fora do LLM como Piso de Qualidade]] — a rota preferida,
  quando ela existe.
- [[Rubrica em Prosa Vira Gabarito de Evidência]] — a mesma conversão aplicada a texto
  acadêmico.
- [[Slop de IA é Convergência de Treino, Não Falta de Gosto]] — o travessão como tell de
  IA, do outro lado da mesma moeda.
- [[Dials Numéricos Tornam Gosto de Design um Parâmetro Declarado]] — o parâmetro que
  essas regras contáveis citam.
- [[Contrato de API que Documenta Comportamento e Custo]] — pôr o critério onde ele é lido.
