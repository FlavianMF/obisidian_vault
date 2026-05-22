---
title: Padrão de Documentação Agêntica Local
type: pattern
tags: [agentic-ai, documentation, automation, second-brain]
created: 2026-05-21
---

# Padrão de Documentação Agêntica Local

Este padrão define como um projeto deve estruturar sua pasta `docs/` para servir como um "segundo cérebro" para agentes de IA, permitindo que a base de conhecimento cresça recursivamente com o projeto.

## 📂 Estrutura Obrigatória e Inicialização
Se a pasta `docs/` não existir, o agente **deve criá-la imediatamente** na primeira sessão. Todo projeto deve conter:
1.  **`PROMPT.md`**: O "System Prompt" local. O agente deve ler este arquivo em cada nova sessão.
2.  **`index.md`**: Mapa de Conteúdo (MOC) do projeto.
3.  **`PRD.md`**: Requisitos e Visão de Produto (Fase A).
4.  **`architecture.md`**: Decisões técnicas e stack (Fase B).
5.  **`engineering_notes.md`**: Log de aprendizados, bugs encontrados e soluções (Recursivo).

## 🤖 Instrução para o Agente (Inserir no `PROMPT.md`)
> "Você é um Engenheiro de Sistemas Agêntico. Antes de codar:
> 1. Leia `docs/index.md` para entender o contexto.
> 2. Se criar uma nova funcionalidade, atualize `docs/PRD.md`.
> 3. Se tomar uma decisão técnica, registre em `docs/architecture.md`.
> 4. Ao final de cada tarefa, adicione aprendizados em `docs/engineering_notes.md`.
> 5. Mantenha a rastreabilidade com o cofre principal: [[Caminho/Para/Nota/No/Vault]]."

## 🔄 Fluxo de Crescimento Recursivo
O agente não apenas lê, mas **escreve seu próprio contexto futuro**. Isso resolve o problema de perda de memória entre sessões longas e garante que a documentação nunca fique desatualizada.

## Links
- [[Engenharia de Sistemas Agêntica]]
- [[00_META/Agent-Instruction]]
