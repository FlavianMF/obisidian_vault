---
title: Template_Nota-de-Etapa
type: template
tags: [template, documentation, definition-of-done, traceability]
created: 2026-09-11
provenance: orbita-platform
---

# Template — Nota de Conclusão de Etapa (`docs/projeto/<Fase>-E<n>-<Tema>.md`)

A etapa não está pronta enquanto esta nota não existe. Ver
[[Nota de Conclusão de Etapa é Entregável, Não Relatório]].

```markdown
# Fase N — E<n>: {{title}}

**Data**: AAAA-MM-DD · **RFC(s)**: [RFC-00N §X](../escopo/rfc/RFC-00N-….md) · **Plano**: [Plano-Fase-N — E<n>](./Plano-Fase-N-….md#âncora-do-heading) · **Worktree**: `worktree-<escopo>` (aguardando validação/merge do usuário)

<!-- Parágrafo-resumo: o que a etapa entregou E o que deliberadamente não entregou. -->

---

## 1. Decisões confirmadas com o usuário nesta sessão
<!-- Toda vez que o agente perguntou e o usuário escolheu. É o que impede a sessão seguinte
     "corrigir" uma escolha deliberada. Pergunta numerada n → commit com sufixo (Qn). -->

## 2. Modelo de dados
## 3. Backend
## 4. Frontend
<!-- Subseções por camada, conforme o que a etapa mexeu. -->

## 5. Achado: <título descritivo do que quebrou e por quê>
<!-- Seção própria, nunca nota de rodapé. Sobe para o playbook no mesmo ciclo. -->

## 6. Padrão novo: <o que passa a valer daqui pra frente>

## 7. Segurança

## 8. Verificação
<!-- O que foi REALMENTE rodado, com número: testes por pacote, cobertura de linhas e de
     ramificações, typecheck, auditoria de dependências. Distinguir o que foi verificado
     AO VIVO do que só passou em teste unitário. -->

## 9. Fora do escopo desta etapa
<!-- O que foi encontrado e deliberadamente não corrigido. Sem isto, vira dívida invisível. -->

## Próximos Passos
<!-- Itens rotulados "**Usuário**:" (⚠️ o que fica com ele) e "**Em aberto**:". -->

---
**Referências**: [Index Geral](../index.md) | [Playbook](./Playbook-de-Desenvolvimento.md) | …
```

Ao fechar: atualizar o `Status` da RFC para `Implementado (E<n>)`, riscar o item no
`Próximos Passos` do plano e acrescentar **uma linha** no `index.md` com `✅`/`🟡`.

## 🔗 Conexões
- [[Nota de Conclusão de Etapa é Entregável, Não Relatório]]
- [[Plano de Fase em Etapas Mescláveis]]
- [[Playbook de Projeto - Erros Já Cometidos Como Artefato]]
