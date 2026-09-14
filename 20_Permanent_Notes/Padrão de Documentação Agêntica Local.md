---
title: Padrão de Documentação Agêntica Local
type: pattern
tags: [agentic-ai, documentation, automation, second-brain]
created: 2026-05-21
provenance: manual
---

# Padrão de Documentação Agêntica Local

Este padrão define como um projeto deve estruturar sua pasta `docs/` para servir como um "segundo cérebro" para agentes de IA, permitindo que a base de conhecimento cresça recursivamente com o projeto.

## 📂 Estrutura Obrigatória e Inicialização
Se a pasta `docs/` não existir, o agente **deve criá-la imediatamente** na primeira sessão.
O mínimo, em qualquer projeto:
1.  **`PROMPT.md`**: O "System Prompt" local. O agente deve ler este arquivo em cada nova sessão (template em `90_Assets/Template_Project_Prompt.md`).
2.  **`index.md`**: Mapa de Conteúdo (MOC) do projeto, com o prompt de início de sessão no topo.
3.  **`PRD.md`**: Requisitos e Visão de Produto (Fase A) — ver [[PRD]].
4.  **`projeto/Playbook-de-Desenvolvimento.md`**: padrões validados e erros já cometidos (o antigo `engineering_notes.md`, com critério de entrada — ver [[Playbook de Projeto - Erros Já Cometidos Como Artefato]]).

Decisão técnica **não** vai num `architecture.md` guarda-chuva: vai numa RFC por decisão,
com a alternativa rejeitada registrada ([[RFC de Produto - Anatomia e Ciclo de Status]]).
Um arquivo único de arquitetura vira o lugar onde tudo envelhece junto.

### Pastas por natureza, quando o projeto cresce
A partir do nível 2 da [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]],
`docs/` se organiza pelo que o documento **é**, não por quando foi escrito:

```
docs/
├── index.md          MOC + prompt de início de sessão
├── escopo/           o quê: intenção do usuário, escopo do sistema, PRD, e escopo/rfc/
├── projeto/          como e quando: plano de fase, notas de etapa, playbook, operação
├── qualidade/        a régua: diretrizes de teste, gates, limites
└── dados/            modelo de dados
```

A cadeia completa de artefatos (intenção → escopo → PRD → RFC-000 → RFCs → plano de fase →
nota por etapa → playbook), os três níveis de aplicação e as convenções de forma estão em
[[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]].

## 🤖 Instrução para o Agente (Inserir no `PROMPT.md`)
> "Você é um Engenheiro de Sistemas Agêntico. Antes de codar:
> 1. Leia `docs/index.md` para entender o contexto.
> 2. Se criar uma nova funcionalidade, atualize `docs/PRD.md`.
> 3. Se tomar uma decisão técnica, registre numa RFC em `docs/escopo/rfc/`, com a alternativa rejeitada.
> 4. Ao final de cada tarefa, adicione ao `docs/projeto/Playbook-de-Desenvolvimento.md` o que custou uma sessão (sintoma + causa + comando exato).
> 5. Mantenha a rastreabilidade com o cofre principal: [[Caminho/Para/Nota/No/Vault]]."

## 🔄 Fluxo de Crescimento Recursivo
O agente não apenas lê, mas **escreve seu próprio contexto futuro**. Isso resolve o problema de perda de memória entre sessões longas e garante que a documentação nunca fique desatualizada.

## Links
- [[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]]
- [[PRD]]
- [[RFC de Produto - Anatomia e Ciclo de Status]]
- [[Playbook de Projeto - Erros Já Cometidos Como Artefato]]
- [[Engenharia de Sistemas Agêntica]]
- [[00_META/Agent-Instruction]]
