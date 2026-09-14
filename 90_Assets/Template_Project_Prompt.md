---
title: 🧠 PROMPT: Instruções para o Agente de Desenvolvimento
type: template
tags: [template, agentic-ai, governance, project-bootstrap]
created: 2026-05-21
provenance: manual
---

# 🧠 PROMPT: Instruções para o Agente de Desenvolvimento

Este arquivo é o seu **contexto mestre** para este projeto (`docs/PROMPT.md`). Leia-o
integralmente antes de iniciar qualquer tarefa.

## 🎯 Sua Missão
Desenvolver este software seguindo os princípios de **Engenharia de Sistemas (NASA/INCOSE)**
e manter `docs/` como o cérebro do projeto.

## 🗂️ A Cadeia de Artefatos

O nível é escolhido **antes** do primeiro documento e declarado ao usuário
([[Cadeia de Artefatos de Projeto - Intenção, RFC, Plano de Fase]]):

| Nível | Quando | Documentos |
|---|---|---|
| 1 — script/ferramenta | tudo o mais | `docs/PRD.md` (meia página) + `docs/projeto/Playbook-de-Desenvolvimento.md` |
| 2 — serviço/feature grande | entrega única, mas com decisão técnica redebatível | + uma RFC + plano de etapas + `index.md` |
| 3 — produto multi-fase | vários atores/áreas, banco com dado real, várias sessões | cadeia completa: escopo do sistema, PRD de release, RFC-000 + RFCs, plano de fase, nota por etapa |

Pastas por natureza: `escopo/` (o quê) · `projeto/` (como e quando) · `qualidade/` (a régua)
· `dados/` (modelo) · `mbse/` (capacidades).

## 📚 Ciclo de Trabalho Obrigatório
1. **Exploração**: leia `docs/index.md` para a hierarquia de documentos, e o
   **Playbook** para não repetir erro já pago.
2. **Alinhamento**: confira `docs/PRD.md` e as RFCs — a solução não pode violar requisito
   nem decisão registrada. Decisão ambígua de alto impacto: pergunte com 2–3 opções
   concretas antes de implementar.
3. **Execução**: em `git worktree` isolada, TDD, commits na worktree. Não mescle — o usuário
   valida e mescla.
4. **Expansão do conhecimento (RECURSIVO)**:
   - Etapa concluída? Nota em `docs/projeto/` ([[Nota de Conclusão de Etapa é Entregável, Não Relatório]]).
   - Armadilha que custou uma sessão? Playbook, com sintoma + causa + comando.
   - Decisão técnica nova? RFC, com a alternativa rejeitada
     ([[RFC de Produto - Anatomia e Ciclo de Status]]).
   - `Status` da RFC e linha do `index.md` atualizados **no mesmo ciclo** — nota
     desatualizada é bug, não dívida.

## 🖇️ Conexão com o Segundo Cérebro (Vault)
Base de conhecimento global em `~/obsidian_vault`, lida por manifest primeiro:
`00_META/manifests/INDEX.md`, depois `grep` em `00_META/manifests/by_type/*.md` — nunca
varredura de pasta inteira. Governança em `~/obsidian_vault/00_META/Agent-Instruction.md`.
Ao final da sessão, destile o generalizável de volta para o vault.

## 🏗️ Padrões Técnicos
- **Isolamento**: containers para ferramentas ([[Docker-out-of-Docker (DooD)]]).
- **Tipagem**: strict typing (TS interfaces / Pydantic), typecheck como gate.
- **Tratamento de erros**: padrão único de resposta, documentado no PRD/RFC.
- **Workflow de dev**: [[Checklist de Bootstrap de Workflow de Desenvolvimento]] (worktree,
  escopo de teste explícito, relatório de CI no próprio pipeline, versionamento e release).

---
*Você está autorizado a atualizar este `PROMPT.md` e outros arquivos em `docs/` para melhorar
sua própria eficiência em turnos futuros.*
