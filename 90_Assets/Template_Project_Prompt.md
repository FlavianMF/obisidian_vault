---
title: 🧠 PROMPT: Instruções para o Agente de Desenvolvimento
type: template
tags: []
created: 2026-05-21
provenance: manual
---

# 🧠 PROMPT: Instruções para o Agente de Desenvolvimento

Este arquivo é o seu **contexto mestre** para este projeto. Leia-o integralmente antes de iniciar qualquer tarefa.

## 🎯 Sua Missão
Desenvolver este software seguindo rigorosamente os princípios de **Engenharia de Sistemas (NASA/INCOSE)** e manter este `docs/` como o seu cérebro de projeto.

## 📚 Ciclo de Trabalho Obrigatório
1.  **Exploração**: Leia `docs/index.md` para entender a hierarquia de documentos.
2.  **Alinhamento**: Verifique o `docs/PRD.md` e `docs/architecture.md` para garantir que sua solução não viole requisitos ou decisões prévias.
3.  **Execução**: Implemente a tarefa de forma cirúrgica.
4.  **Expansão do Conhecimento (RECURSIVO)**:
    - Criou um novo padrão? Documente em `docs/patterns/`.
    - Encontrou um bug difícil? Registre em `docs/engineering_notes.md` como um "Trap".
    - Atualizou a API? Atualize `docs/api_design.md`.

## 🖇️ Conexão com o Segundo Cérebro (Vault)
Consulte sempre a base de conhecimento global do Flavian em:
`docs/second_brain/00_META/Agent-Instruction.md`

## 🏗️ Padrões Técnicos
- **Isolamento**: Use containers (Docker) para ferramentas.
- **Tipagem**: Strict typing em 100% (TS Interfaces / Pydantic).
- **Tratamento de Erros**: Padrão JSON `{error, message, detail}`.

---
*Você está autorizado a atualizar este PROMPT.md e outros arquivos em docs/ para melhorar sua própria eficiência em turnos futuros.*
