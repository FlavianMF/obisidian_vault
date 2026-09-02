---
title: Decoder JSON em Go Trata Chave Ausente e Null Como Idêntico
type: trap
tags: [go, golang, json, api-compatibility, openai-compatible]
created: 2026-09-02
provenance: capella_llm_window
project: capella_llm_window
---

# Decoder JSON em Go Trata Chave Ausente e Null Como Idêntico

## Sintoma

Um client que serializa um campo JSON como `null` explícito (em vez de
omitir a chave) pra corrigir um erro de validação de schema contra um
backend escrito em Go, e o mesmo erro continua acontecendo idêntico —
`"invalid message content type: <nil>"` (ou similar) tanto antes quanto
depois da correção.

Caso real: um plugin de chat mandava mensagens do tipo assistant-só-com-
tool-call sem a chave `content` (a correção "óbvia" pareceria ser incluir
`"content": null` explícito, seguindo o schema OpenAI). Contra um backend
Go (Ollama), isso não resolveu nada — o mesmo erro `400` voltou.

## Causa

`encoding/json` do Go, ao decodificar um valor desconhecido pra
`interface{}` (ou pra um campo de struct do tipo `interface{}`/`any`),
produz o mesmo resultado — `nil` — tanto quando a chave está **ausente**
quanto quando ela está presente com valor **`null`** explícito. Um type
switch/assertion Go típico:

```go
switch content := msg.Content.(type) {
case string:
    ...
case []any:
    ...
default:
    return fmt.Errorf("invalid message content type: %v", content)
}
```

cai no `default` nos dois casos igualmente — `%v` de um `nil` interface
imprime literalmente `<nil>`, que é exatamente o texto que aparece na
mensagem de erro. Pra esse tipo de decoder, "ausente" e "null" são o
mesmo valor: não existe diferença observável entre eles do lado do
servidor.

## Fix

Não adianta trocar entre omitir a chave e mandar `null` explícito — os
dois batem no mesmo `default`. Só um valor de um tipo que o `switch`
realmente trata resolve (nesse caso, string vazia `""` em vez de `null`
pro campo problemático) — mesmo que `null` seja tecnicamente válido pelo
schema documentado (ex. OpenAI aceita `content: null` pra uma mensagem
assistant só-com-tool-call).

## Generalização

Ao debugar incompatibilidade de schema JSON contra um backend
desconhecido: se o backend é (ou pode ser) escrito em Go, considerar que
"campo ausente" e "campo com valor `null`" podem ser estritamente
indistinguíveis do lado do servidor — uma correção que só troca entre os
dois não resolve nada, mesmo que pareça correta comparando com a spec do
schema (que geralmente foi desenhada pensando em decoders mais permissivos,
tipo JS/Python). Confirmar contra o comportamento real do servidor (uma
requisição de teste), não só contra a documentação do schema.

## 🔗 Conexões
- [[Ollama Ignora Tamanho de Contexto Enviado por Request]]
