---
title: Detector Determinístico Fora do LLM como Piso de Qualidade
type: pattern
tags: [agentic-ai, quality, hooks, linter, design, claude-code, ci]
created: 2026-09-20
provenance: impeccable
verified: 2026-09-20 via execução local do binário (engine 0.1.5) sobre fixture de slop
---

# Detector Determinístico Fora do LLM como Piso de Qualidade

**Num domínio que parece subjetivo, quase sempre existe um subconjunto mecânico: coisas
que ou estão lá ou não estão, verificáveis sem julgamento. Esse subconjunto não deve ser
pedido ao LLM — deve virar um binário com exit code.** O LLM então só gasta token no que
sobra, que é o julgamento de verdade. [[Impeccable]] faz isso com design de interface: 61
regras em Rust, sem Node e sem API key em runtime, rodando sobre HTML/CSS.

O que o binário decide sozinho: contraste abaixo de 4.5:1, `border-left: 6px` num card
arredondado, `background-clip: text` com gradiente, nível de heading pulado, `line-height`
1.1, texto funcional abaixo de 11px, card dentro de card, fonte fora do `DESIGN.md`. O que
ele nunca decide: se a direção está certa. Esses dois conjuntos não competem.

## Por que virar binário e não regra em prompt

Regra em prompt é probabilística: o modelo pode aplicá-la, esquecê-la ou negociar com ela.
Regra em binário é a mesma resposta sempre, com custo zero de contexto, e o mesmo artefato
serve três consumidores diferentes sem ser reescrito:

- **hook do harness**, que injeta o achado no contexto do agente logo depois da edição;
- **CLI manual** (`impeccable detect --json <dir>`), que o desenvolvedor roda quando quer;
- **CI**, que lê o exit code — `0` limpo, `2` achados, `1` falha de scan, com falha
  operacional tendo precedência num scan parcial de múltiplos alvos.

Saída humana vai para **stderr** justamente para deixar stdout livre para o JSON. É o
mesmo cuidado de contrato de [[Contrato de API que Documenta Comportamento e Custo]].

## Dois níveis, para não interromper à toa

A separação que faz o hook ser tolerável: nem toda regra merece interromper uma edição.

- **Nível imediato**, no `PostToolUse`: só o mecânico e inequívoco — imagem quebrada,
  conteúdo estourando ou cortado, falha de contraste, gradient text, drift do design
  system. Coisa que você quer saber antes de escrever o próximo arquivo.
- **Passe profundo**, no `Stop`: o conjunto inteiro de regras sobre todos os arquivos de
  UI tocados na sessão, **deduplicado contra o que o nível imediato já reportou**. Cadência
  de copy, gosto de paleta e ritmo de layout entram aqui. Sessão sem nada a dizer termina
  em silêncio.

Um terceiro nível existe implicitamente: o que scanner nenhum pega (o `craft-floor.md` da
skill) fica no prompt mesmo, carregado antes de qualquer edição de UI. A regra de partição
é essa — **prompt só recebe o que não dá para detectar**.

## Achado não é ordem de ignorar

O hook nunca escreve config sozinho. Cada achado é triado em exatamente três saídas:

1. **Problema real** — corrige. Nunca se adiciona um ignore para pular uma correção.
2. **Falso positivo ou exceção sancionada** — persiste o ignore **mais estreito possível**
   com a evidência nomeada no `--reason` (`"quem decidiu: evidência"`), e declara isso na
   resposta. A escada de escopo importa: `ignore-value <regra> <valor>` <
   `ignore-value <regra> "*" --file <glob>` < `ignore-file <glob>` < `ignore-rule <id>`.
   Os dois últimos silenciam demais para o agente decidir sozinho — pergunta primeiro.
3. **Incerto** — deixa o achado de pé e pergunta em uma linha. Uma pergunta custa menos
   que o hook disparando de novo em toda edição seguinte.

Ignores compartilhados vão para o arquivo versionado; exceções privadas para o gitignored.
Comentário inline (`impeccable-disable <regra>: motivo`) fica reservado para quando a
dispensa precisa viajar junto com um arquivo que sai do repositório.

## Generaliza

O par vale para qualquer domínio onde um agente produz artefato com qualidade avaliável:
schema de API, migração de banco, texto jurídico, acessibilidade, convenção de commit.
Pergunta de projeto: *o que da minha rubrica um programa consegue checar?* Ver
[[Rubrica em Prosa Vira Gabarito de Evidência]] e [[Teste como Plugin no Fundo da Cadeia]] —
a mesma ideia de pôr o critério num lugar executável em vez de num lugar persuasivo.
O acoplamento hook/renderizador é o de
[[Hook Escreve Estado, Renderizador Lê Tudo Num Passe]]; a interceptação por evento é a de
[[Toda Chamada na API é um Evento Interceptável]]. Quando não há binário disponível e a
regra tem mesmo que ficar no prompt, o melhor que sobra é escrevê-la como limiar ou
contagem: [[Regra Gradual é Ignorada pelo Agente, Regra Binária é Obedecida]].
