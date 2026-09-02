---
title: Detecção Ao Vivo de Janela de Contexto do Ollama via api-ps e api-show
type: pattern
tags: [ollama, llm, context-window, openai-compatible, api-design]
created: 2026-09-02
provenance: capella_llm_window
project: capella_llm_window
---

# Detecção Ao Vivo de Janela de Contexto do Ollama via api-ps e api-show

## Problema

Um client que precisa saber o tamanho real de contexto de um modelo
Ollama pra decisões internas (quando compactar histórico, mostrar % de
uso) não pode confiar só num catálogo estático tipo models.dev — esse só
sabe o máximo *arquitetural* do modelo, não o `num_ctx` de verdade que o
servidor vai carregar (que pode ser bem menor, ver
[[Ollama Ignora Tamanho de Contexto Enviado por Request]]).

## Padrão

Cascata de duas chamadas na API nativa do Ollama (fora do `/v1`, direto
em `http://host:porta/api/...`), nunca adivinha, sempre cai pro próximo
passo se o anterior não respondeu:

1. **`GET /api/ps`** — modelos carregados na memória *agora*. Cada
   entrada já vem com `context_length` top-level: o valor real de
   runtime. Mais preciso possível, mas só populado depois que o modelo já
   foi usado ao menos uma vez nesse processo do Ollama (e ainda não
   ociosou) — vem vazio (`{"models": []}`) num servidor recém-iniciado ou
   logo depois de abrir uma tela de configuração, mesmo o modelo existindo
   em disco.
2. **`POST /api/show`** (fallback quando 1 não achou nada) — `{"model": "nome"}`
   no corpo. Funciona pra qualquer modelo que o Ollama conhece em disco,
   carregado ou não. Dentro da resposta, prioriza:
   - `parameters` (string estilo Modelfile, "chave valor" por linha) —
     procura uma linha `num_ctx N` explícita, é o valor que *vai* carregar
     de verdade se foi customizado.
   - senão, `model_info` — chave dinâmica prefixada pela arquitetura
     (`"<família>.context_length"`, ex. `"qwen2.context_length"`,
     `"gemma4.context_length"` — não é uma chave fixa, precisa escanear
     por sufixo `.context_length`). É o máximo arquitetural, real mas não
     necessariamente o que vai ser alocado.

Bônus: `/api/ps` e `/api/show` compartilham o mesmo formato de objeto
`details` (`parameter_size`, `quantization_level`, `family`) — só
`capabilities` (completion/tools/vision) é exclusivo do `/api/show`.

## Quando usar

Qualquer client/plugin OpenAI-compatible que fale com Ollama e precise de
metadados reais do modelo (contexto, tamanho, capabilities) sem depender
de um catálogo externo estático ou pedir pro usuário digitar na mão.
Sempre com timeout curto e fallback silencioso — é *best effort*: se não
é servidor Ollama, ou tá fora do ar, cai pro próximo nível da cadeia de
prioridade do client (nesse projeto: detecção ao vivo > models.dev >
fallback fixo).

## 🔗 Conexões
- [[Ollama Ignora Tamanho de Contexto Enviado por Request]]
