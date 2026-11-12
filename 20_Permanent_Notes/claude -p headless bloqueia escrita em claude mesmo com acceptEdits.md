---
title: "claude -p headless bloqueia escrita em .claude/ mesmo com acceptEdits"
type: permanent
created: 2026-11-10T14:05:40
moc: "Design de Interface com Agente"
tags: [claude, headless, fluxos, permissões]
source_inbox: "b3021e89-claude-p-headless-bloqueia-escrita-em-claude-mesmo-com-accep.md"
tier: "L2"
score: 0.756
---

# claude -p headless bloqueia escrita em .claude/ mesmo com acceptEdits

Em teste headless de prompt que grava em .claude/PRPs/, o harness trata .claude/ como caminho sensível e nega Write/mkdir; o agente grava em outro lugar. O motor de fluxos precisa rodar nós com permissão explícita para essa pasta.

# claude -p headless bloqueia escrita em .claude/ mesmo com acceptEdits

## Contexto
Durante um teste headless de prompt que grava em `.claude/PRPs/`, foi observado que o harness nega a operação de Write/mkdir para a pasta `.claude/`. O agente, por outro lado, continua gravando em um local alternativo.

## Detalhes
- **Tipo**: trap
- **Projeto**: feat-agent-flows
- **Fonte**: agent
- **Contagem**: 1
- **Sessões**: 1
- **IDs de Sessão**: c250fbc6-58a1-4095-bfd7-ffb2d7aee27f

## Armadilhas
O motor de fluxos precisa rodar nós com permissão explícita para a pasta `.claude/` para evitar bloqueios na escrita.

## Próximos passos
- Verificar as permissões da pasta `.claude/`.
- Configurar o motor de fluxos para permitir operações de Write/mkdir na pasta `.claude/`.
- Realizar testes adicionais para garantir que o problema foi resolvido.

## Conexões
- [[Design de Interface com Agente]]
