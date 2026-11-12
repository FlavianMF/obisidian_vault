---
title: "Prompt de fase em motor sem usuário não pode 'parar e perguntar"
type: permanent
created: 2026-11-10T14:07:17
moc: "Design de Interface com Agente"
tags: [agent, ecc, traycer, prompts]
source_inbox: "0d1d9ac0-prompt-de-fase-em-motor-sem-usuario-nao-pode-parar-e-pergunt.md"
tier: "L2"
score: 0.786
---

# Prompt de fase em motor sem usuário não pode 'parar e perguntar

Ao adaptar comandos interativos do ECC para filhos do Traycer, troque portões 'pare e pergunte' por registro de suposição conservadora e falha/parada com motivo. Remova passos que movem a entrada e quebram retry.

# Prompt de fase em motor sem usuário não pode 'parar e perguntar'

## Contexto
Ao adaptar comandos interativos do ECC (prp-plan, prp-implement) para filhos do Traycer, é necessário ajustar o comportamento dos portões 'pare e pergunte'. O objetivo é garantir que o motor não continue em uma fase sem usuário e que seja capaz de registrar suposições conservadoras e falhar/parar com motivo apropriado.

## Detalhes
- **Portões 'pare e pergunte'**: Substituir por registro de suposição conservadora e falha/parada com motivo.
- **Remoção de passos**: Eliminar passos que movem a entrada (arquivar plano) e quebram retry.

## Próximos passos
1. Implementar a substituição dos portões 'pare e pergunte' pelo registro de suposição conservadora e falha/parada.
2. Remover os passos que movem a entrada e quebram retry.
3. Testar a implementação em ambientes de desenvolvimento e produção para garantir o comportamento desejado.

## Conexões
- [[Design de Interface com Agente]]
