---
title: Skill: Sincronização de Conhecimento Recursiva
type: pattern
tags: [agentic-ai, knowledge-management, second-brain]
created: 2026-05-21
provenance: manual
---

# Skill: Sincronização de Conhecimento Recursiva

Esta skill define o comportamento obrigatório de atualização de bases de conhecimento após a conclusão de qualquer desenvolvimento.

## 🤖 Comportamento Esperado
Ao finalizar uma tarefa (antes de se dar por satisfeito), o agente deve:

1.  **Update Local Brain**:
    - Atualizar `docs/engineering_notes.md` com novos "Traps" ou "Decisions".
    - Atualizar `docs/architecture.md` se a estrutura mudou.
2.  **Update Global Brain (Vault)**:
    - Se um padrão genérico foi descoberto (ex: uma nova forma de lidar com OAuth), o agente deve criar ou atualizar a nota correspondente em `docs/second_brain/20_Permanent_Notes/`.
    - Usar o campo `provenance:` para citar o projeto de origem.
3.  **Cross-Linking**: Garantir que a nota do projeto no vault principal aponta para as novas descobertas.

## 🔗 Conexões
- [[Padrão de Documentação Agêntica Local]]
- [[00_META/Agent-Instruction]]
