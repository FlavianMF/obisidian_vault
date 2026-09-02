---
title: Ollama Ignora Tamanho de Contexto Enviado por Request
type: trap
tags: [ollama, llm, context-window, openai-compatible, num_ctx]
created: 2026-09-02
provenance: capella_llm_window
project: capella_llm_window
---

# Ollama Ignora Tamanho de Contexto Enviado por Request

## Sintoma

Um campo de "override de contexto" no client (qualquer coisa que tente
mandar um tamanho de janela de contexto no corpo do request pro endpoint
`/v1/chat/completions` do Ollama, seja `num_ctx` top-level, seja aninhado
em `options.num_ctx`) simplesmente não muda o comportamento real — o
modelo continua truncando no mesmo tamanho de sempre.

## Causa

Confirmado direto na doc oficial do Ollama
(`docs.ollama.com/api/openai-compatibility`): o endpoint OpenAI-compatible
aceita alguns campos Ollama-specific como top-level (`reasoning_effort`,
`reasoning`, `seed`) — `num_ctx` **não está nessa lista**, de propósito. A
própria doc diz que a API no formato OpenAI não tem como setar tamanho de
contexto; é preciso um Modelfile customizado.

Tentar contornar via `options`/`extra_body` (como faz o client Python da
OpenAI) também não funciona — issue real do próprio Ollama
([ollama/ollama#6544](https://github.com/ollama/ollama/issues/6544))
confirma que isso chega no servidor como campo solto (`extra_json`), não
mesclado no corpo real do request.

## Fix

Não tem fix client-side. O tamanho de contexto é decidido no servidor:

- **Padrão automático por VRAM** (sem nada configurado): `OLLAMA_CONTEXT_LENGTH=0`
  (sentinela) faz o Ollama escolher pela VRAM disponível — 4096 tokens
  abaixo de ~23GiB, 32768 a partir de ~23GiB, 262144 a partir de ~47GiB.
- **Mudar o padrão do servidor inteiro**: variável de ambiente
  `OLLAMA_CONTEXT_LENGTH=N`, setada **antes** de `ollama serve` (não
  adianta exportar depois no shell, e não funciona só exportar se o
  Ollama roda como serviço systemd — precisa estar no ambiente do
  processo do servidor mesmo).
- **Mudar só um modelo específico**: Modelfile customizado com
  `PARAMETER num_ctx <N>`, `ollama create meu-modelo -f Modelfile`, usar
  `meu-modelo` como nome do modelo nos requests.

## Generalização

Qualquer client OpenAI-compatible pra Ollama que precise saber (não
mudar) o contexto real de um modelo já carregado deve **ler**, não tentar
setar — via `GET /api/ps` (`context_length` do modelo carregado agora,
runtime de verdade) ou `POST /api/show` (funciona mesmo sem o modelo
carregado, mas retorna o máximo arquitetural em `model_info`, que pode
ser maior do que o que realmente vai ser alocado sob os tiers de VRAM
acima). Ver [[Detecção Ao Vivo de Janela de Contexto do Ollama via api-ps e api-show]].

## 🔗 Conexões
- [[Detecção Ao Vivo de Janela de Contexto do Ollama via api-ps e api-show]]
- [[Campo de Settings Só Deve Ser Editável Se Aplicar de Verdade]]
