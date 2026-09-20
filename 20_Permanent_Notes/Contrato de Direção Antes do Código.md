---
title: Contrato de Direção Antes do Código
type: pattern
tags: [design, agentic-ai, project-methodology, documentation, brief]
created: 2026-09-20
provenance: impeccable
---

# Contrato de Direção Antes do Código

**Antes de escrever a primeira linha de um artefato criativo, o agente registra a direção
escolhida como um contrato curto e verificável — e o último bloco desse contrato é a
condição de saída.** Em [[Impeccable]] isso se chama *direction contract*: seis blocos,
cerca de 150 palavras no total, gravados no *surface brief* daquela rota ou artefato.

Os seis blocos:

1. **THESIS** — a única ideia que esta superfície carrega, **e o arranjo padrão da
   categoria que ela recusa**. A recusa explícita é metade do valor: sem ela, "landing
   page de ferramenta" já preenche o vazio sozinha.
2. **OWN-WORLD** — a paleta e a linguagem de componentes, específicas o bastante para
   serem reconhecíveis com todo o conteúdo removido.
3. **STORY** — o que o visitante entende, acredita e faz.
4. **FIRST VIEWPORT** — a composição exata: o que fica onde, em que escala, e onde está a
   ação primária.
5. **FORM** — a forma escolhida, a posição dela na lista ordenada de alternativas, e a
   chave de seed que a produziu.
6. **FINISH** — a condição de saída, literal: *não revisado e não documentado é não
   terminado; este build acaba com o finish review, o veredito, o `DESIGN.md` e cada
   raster entregue carregando sua proveniência.*

## Por que isso funciona

**Um bloco que soa como *mood* prova que a direção ainda não foi decidida.** Esse é o
teste barato embutido no formato: "clean, modern, trustworthy" não passa em FIRST
VIEWPORT nem em OWN-WORLD, e a falha aparece antes de custar implementação. Decidir
depois, no meio do código, é onde o agente cai no default da categoria.

O bloco FINISH resolve um problema diferente e mais teimoso: **uma página que parece
pronta com o FINISH em aberto não está terminada, está abandonada na linha de chegada.**
Sessões longas perdem o critério de conclusão; escrever a condição de saída no mesmo
artefato que o agente recarrega a cada sessão faz o critério sobreviver ao contexto.
O revisor de finish depois audita o render **contra o contrato**, não contra o gosto dele.

## A regra de vazamento

O contrato é metadado de desenvolvimento e **nunca** entra no artefato entregue: nem em
comentário HTML ou de framework, nem em DOM escondido, `<template>`, atributo `data-*`,
JSX renderizado, props serializadas, payload de RSC, bundle, metadata, JSON-LD, texto
só-para-acessibilidade, ou arquivo servido ao lado. Compilador que remove metadado de
desenvolvimento **não é fronteira de segurança** — é otimização, e otimização muda.
Quem precisa do contrato (revisor, documenter) recebe do brief.

## Generaliza

Vale para qualquer build criativo ou aberto conduzido por agente, não só design: o par
"direção decidida e escrita antes" + "condição de saída no mesmo lugar" é o que impede
tanto a deriva para o default quanto o polimento infinito. É o mesmo movimento de
[[Plano de Fase em Etapas Mescláveis]] (aceite escrito antes da execução) e de
[[Cadeia de Artefatos Aplicada a Finanças Pessoais]], um degrau abaixo em granularidade.
O catálogo de defaults que a THESIS precisa recusar está em
[[Slop de IA é Convergência de Treino, Não Falta de Gosto]]; a disciplina de parar está em
[[Verificação em Passes Limitados, Não em Loop]]. Erros já pagos viram
[[Playbook de Projeto - Erros Já Cometidos Como Artefato]].
