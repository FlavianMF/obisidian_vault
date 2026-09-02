---
title: Campo de Settings Só Deve Ser Editável Se Aplicar de Verdade
type: pattern
tags: [ux, settings, agentic-ai, product-design]
created: 2026-09-02
provenance: capella_llm_window
project: capella_llm_window
---

# Campo de Settings Só Deve Ser Editável Se Aplicar de Verdade

## Contexto

Um plugin de chat (Capella AI Chat) subiu um campo de texto editável
"Context window override" nas Settings, pra deixar o usuário corrigir a
estimativa de tamanho de contexto quando a detecção automática não sabia.
Só depois, testando contra Ollama de verdade, ficou claro que **nenhum**
backend OpenAI-compatible expõe como configurar isso por request — o
número digitado nunca saía do plugin, só alimentava a contabilidade
interna dele (ver [[Ollama Ignora Tamanho de Contexto Enviado por Request]]).

## Padrão

Reação do usuário ao entender isso: "não faz sentido ter um campo
editável de contexto se não dá pra aplicar de fato... deve virar apenas
informativo." O campo virou um `Label` read-only mostrando o valor
detectado + a origem (ex. "4096 tokens (detected live from the
backend)"), sem caixa de texto nenhuma.

Regra geral: **um controle editável numa UI de configuração implica pro
usuário que aquele valor tem efeito real em algo**. Se o valor só
alimenta contabilidade/estimativa interna do próprio app (nunca é
enviado/aplicado em nenhum sistema externo), expor como editável é
enganoso — mesmo que a intenção original (permitir correção manual) seja
razoável. A correção certa nesse caso não foi "melhorar a UX do campo",
foi remover a editabilidade e deixar só leitura.

## Quando aplicar

Antes de adicionar qualquer controle editável (texto, combo, checkbox)
numa tela de configuração: confirmar que o valor realmente chega em algo
externo (API, arquivo de config de outro sistema, processo filho) ou tem
efeito observável em comportamento real. Se é só pra exibição/estimativa
interna, é status read-only, não input.

## 🔗 Conexões
- [[Ollama Ignora Tamanho de Contexto Enviado por Request]]
