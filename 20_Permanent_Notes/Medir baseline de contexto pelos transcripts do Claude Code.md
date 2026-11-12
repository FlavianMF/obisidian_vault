---
title: "Medir baseline de contexto pelos transcripts do Claude Code"
type: permanent
created: 2026-11-10T14:33:15
moc: "Design de Interface com Agente"
tags: [claudie, code, baseline, context, transcripts]
source_inbox: "1dd8b244-medir-baseline-de-contexto-pelos-transcripts-do-claude-code.md"
tier: "L1"
score: 0.707
---

# Medir baseline de contexto pelos transcripts do Claude Code

Sem API key, o campo usage da 1a resposta de cada sessão em ~/.claude/projects/*/*.jsonl mede o baseline exato. Os registros api-request-shape e api-request-blob dao os caracteres por componente (system, tools, mensagens). Dedupe por message.id. Razão medida: ~2,85 chars/token em JSON.

# Medir baseline de contexto pelos transcripts do Claude Code

## Contexto
Para medir o baseline exato do contexto utilizado pelo Claude Code, é necessário analisar os dados dos transcripts sem a necessidade de uma API key. Esse método permite obter informações precisas sobre a quantidade de caracteres usados em diferentes componentes da interação.

## Detalhes
O campo `usage` na primeira resposta de cada sessão em `~/.claude/projects/*/*.jsonl` fornece o baseline exato do contexto. Os registros `api-request-shape` e `api-request-blob` detalham os caracteres por componente, incluindo `system`, `tools` e `mensagens`. Para evitar duplicatas, é necessário deduplicar as mensagens usando `message.id`.

A razão para essa medida é que a conversa é codificada em JSON, com uma média de aproximadamente 2,85 caracteres por token.

## Próximos passos
1. **Analisar os dados**: Examinar os arquivos JSONL para coletar as informações necessárias.
2. **Deduplicação**: Implementar um processo para remover duplicatas de mensagens usando `message.id`.
3. **Cálculo do baseline**: Calcular o total de caracteres usados em cada componente da interação.
4. **Validação**: Validar os resultados para garantir a precisão da medição.

## Conexões
- [[Design de Interface com Agente]]
