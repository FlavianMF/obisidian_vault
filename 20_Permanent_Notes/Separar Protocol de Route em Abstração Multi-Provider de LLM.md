---
title: Separar Protocol de Route em Abstração Multi-Provider de LLM
type: pattern
tags: [llm, multi-provider, adapter-pattern, api-design, architecture]
created: 2026-09-08
provenance: projetos_ita
project: projetos_ita
---

# Separar Protocol de Route em Abstração Multi-Provider de LLM

Ao construir uma camada que fala com múltiplos providers de LLM (Anthropic,
OpenAI, Bedrock, modelos locais, etc.), separar duas responsabilidades que
tendem a se misturar num adapter único por provider:

- **Protocol** — como transformar o payload pro formato de wire daquele
  provider (ex.: `anthropic/messages` vs. `openai/responses`), e como
  normalizar a resposta/stream de volta pro formato interno único.
- **Route** — pra onde mandar (endpoint), com que auth, com que config
  (timeout, retry) — decisões de "onde" e "como conectar", não "que
  formato".

**Por que importa**: adicionar um provider novo vira "escrever um
transformador de protocolo + declarar uma rota", sem tocar a lógica de
streaming/normalização de evento que já existe. Todo o resto do sistema
(loop de agente, tool-calling, gestão de contexto) só vê o formato de
evento normalizado — nunca o formato específico de nenhum provider.

**Como fica concretamente** (caso observado em [[opencode]]):
- Package próprio de LLM mantém `protocols/` e `route/` como pastas
  separadas; cada adapter de provider (Anthropic, OpenAI, Bedrock, Azure,
  Google, OpenRouter, xAI, genérico OpenAI-compatible) compõe as duas
  peças.
- Todo provider transmite eventos pelo **mesmo formato normalizado**,
  independente do backend — o loop de agente nunca faz `if provider ===
  "anthropic"`.
- Extração estruturada (`generateObject()`) é forçada via tool-call em
  *todo* provider, em vez de usar o "modo JSON" específico de cada um —
  comportamento uniforme mesmo quando o provider oferece um atalho nativo
  diferente.
- Camada complementar (não deste pattern, mas resolve um problema
  adjacente): uma segunda integração via SDK de terceiro (Vercel AI SDK)
  cobre a cauda longa de providers community-maintained sem escrever
  adapter manual pra cada um — os dois mecanismos coexistem, um pra
  providers "de primeira classe" com controle fino, outro pra cobertura
  ampla.

**Quando usar**: qualquer harness/ferramenta que precise suportar mais de
2-3 providers de LLM de forma extensível, especialmente se streaming e
tool-calling precisam de comportamento idêntico não importa o provider por
trás.

## 🔗 Conexões
- [[opencode]]
