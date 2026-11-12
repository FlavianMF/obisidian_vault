---
title: "Motor de fluxo: sucesso da fase = saída mudou desde o send"
type: permanent
created: 2026-11-10T14:08:17
moc: "Design de Interface com Agente"
tags: [agent, flows, t3-t4]
source_inbox: "75893f53-motor-de-fluxo-sucesso-da-fase-saida-mudou-desde-o-send.md"
tier: "L1"
score: 0.706
---

# Motor de fluxo: sucesso da fase = saída mudou desde o send

Grave a assinatura (mtime+tamanho) das saídas antes do send. Dê o turno por encerrado só com agente ocioso E resposta nova no transcript ou saída alterada. Evita falha falsa e filho duplicado na corrida logo após o send; arquivo velho não conta como sucesso.

# Motor de fluxo: sucesso da fase = saída mudou desde o send

## Contexto
O objetivo é implementar um mecanismo para determinar o sucesso de uma fase em um motor de fluxo. O sucesso é definido pela mudança na assinatura (mtime+tamanho) das saídas antes do envio (`send`).

## Detalhes
1. **Gravação da assinatura**: Antes de enviar a saída, gravar a assinatura (mtime+tamanho) da saída.
2. **Determinação do sucesso**: O turno é considerado encerrado se o agente estiver ocioso e houver uma nova resposta no transcript ou uma mudança na assinatura da saída.
3. **Prevenção de falhas falsas e duplicação**: Evitar que a corrida seja marcada como concluída logo após o `send` se o arquivo for velho, não contando como sucesso.

## Próximos passos
- Implementar a gravação da assinatura das saídas.
- Adicionar a lógica para determinar o sucesso com base na assinatura e no estado do agente.
- Testar a implementação em diferentes cenários para garantir que não haja falhas falsas ou duplicação.

## Conexões
- [[Design de Interface com Agente]]
